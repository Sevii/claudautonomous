# Post-training Z-Image Turbo

A practical guide for adapting **Z-Image-Turbo** (Tongyi-MAI's 6B single-stream
DiT, distilled to 8 NFE) to new characters, styles, or concepts — without
breaking the model's fast inference path.

Sources are listed at the bottom. Numbers below are taken from the official
HF blog, the model card, the Ostris AI Toolkit notes, and community reports
on RTX 30/40/50 hardware.

---

## 1. What "Z-Image Turbo" actually is

| Piece                  | Value                                                                  |
|------------------------|------------------------------------------------------------------------|
| Architecture           | Single-stream DiT (text + visual semantic + VAE tokens concatenated)   |
| Parameters             | ~6 B in the DiT                                                        |
| Base model             | Z-Image (50-step flow-matching foundation)                             |
| Distillation           | **Decoupled-DMD** → 8 NFE; followed by **DMDR** (DMD + RL)             |
| Inference              | `num_inference_steps=9` (= 8 DiT forwards), `guidance_scale=0.0`, bf16 |
| VRAM for inference     | ~16 GB bf16; 6–8 GB with int4 quants                                   |
| License                | Apache-2.0                                                             |

The official model card explicitly marks **Turbo as "N/A" for fine-tuning** and
recommends `Z-Image` (the 50-step base) if you can use it. The community
trains Turbo anyway — it works, but every recipe below exists to work around
the same problem:

> Updating DiT weights (full FT or naive LoRA) disrupts the distilled
> acceleration trajectory. The result is a model that looks fine at 30 steps
> with CFG≈2 but is washed out / structurally broken at 8 steps with CFG=0.

So "post-training Z-Image Turbo" is really a choice among four recipes that
trade off training simplicity vs. preserving the 8-step path.

---

## 2. The four post-training schemes (from the official HF blog)

| # | Scheme                                        | Acceleration at inference?    | Complexity | When to use                                                  |
|---|-----------------------------------------------|-------------------------------|------------|--------------------------------------------------------------|
| 1 | **Standard SFT** only                         | ❌ (need 30 steps, CFG 2)     | Low        | You don't care about latency.                                |
| 2 | **Differential LoRA** on top of a training adapter | ✅ (8 steps, CFG 0/1)    | Low        | Light style/concept tweaks, low VRAM.                        |
| 3 | **SFT + Trajectory-Imitation Distillation**   | ✅                            | High       | Production quality at 8 steps.                               |
| 4 | **SFT + DistillPatch LoRA at inference** ⭐   | ✅                            | Low–Med    | Default recommendation — train freely, patch speed back in.  |

Scheme 4 is what most public LoRAs ship as: you train a normal LoRA against
the Turbo weights, then at inference you load *both* your LoRA *and* a
"DistillPatch"/"training adapter" LoRA that restores the distilled trajectory.

Ostris publishes such an adapter under `ostris/zimage_turbo_training_adapter`
(v1 and v2); v2 is the current community default.

---

## 3. Compute required

Compute is dominated by (a) DiT forward/backward at 1024² and (b) how many
steps you run. Below are the configurations people actually use; treat them
as a menu, not a spec.

### LoRA (Schemes 2 / 4) — the realistic case

| GPU            | VRAM | Setup                                                | Time @ 3k steps  | Notes                                                  |
|----------------|------|------------------------------------------------------|------------------|--------------------------------------------------------|
| RTX 5090       | 32 GB| fp16 weights, no quant, rank 16, batch 1, 1024²      | **15–22 min**    | Fastest publicly reported (RunPod Ostris template).    |
| RTX 4090       | 24 GB| fp16, rank 16, batch 1, gradient checkpointing       | ~45–60 min       | Comfortable headroom.                                  |
| RTX 3090       | 24 GB| fp16, rank 16, batch 1, grad ckpt, 1 sample / 250 st | **~60 min**      | Sampling fewer preview images keeps it inside the hour.|
| RTX 3060 12 GB | 12 GB| int8 base + low-VRAM mode + rank 8, batch 1          | ~2–3 h           | Works (see Tongyi-MAI/Z-Image #36) but iterate slowly. |
| RTX 3060 8 GB  | 8 GB | NF4 / int4 quant base, rank 8, grad ckpt             | ~3–5 h           | Tight; expect occasional OOMs at 1024².                |

Rule of thumb:

* **Lower bound** to actually train at 1024²: **12 GB VRAM** with int8 + rank 8 + gradient checkpointing.
* **Comfortable**: **24 GB** (3090/4090) at fp16, rank 16.
* **Fast**: **32 GB** (5090/H100/A100-40 also fine).
* Disk: budget **~100 GB** for caches, VAE-encoded latents, and checkpoints.

### Full SFT (Scheme 1 or 3 without LoRA)

Realistic only on multi-GPU 80 GB nodes:

* 1× H100 80 GB (or A100 80 GB) per replica, bf16, batch 1, grad ckpt.
* For Scheme 3 (SFT + Trajectory-Imitation Distillation) plan **2× the
  compute of plain SFT**: one stage to teach the concept, one to
  re-distill the 8-step trajectory using the post-SFT model as student and
  the original Z-Image as teacher.
* Public examples use 4–8 H100s for several hours per epoch on a few-thousand
  image dataset. There are no official numbers — Tongyi has not released the
  pre-training recipe.

If you're not at a lab with 8×H100, **don't full-FT**. Do Scheme 4.

---

## 4. Dataset: how many images, and how to annotate them

The two main public recipes disagree on captioning. Both work; pick one.

### 4.1 Identity / single-concept LoRA (Ostris AI Toolkit recipe)

* **Count**: as few as **5–15 images**; 9 × 1024² is a proven floor for a
  reliable character imprint. 20–60 is the sweet spot for robust identity.
* **Resolution**: 1024×1024 (match the distilled training resolution). Square
  crop or letterbox; don't go below 1024 on the long edge.
* **Quality > quantity**: grainy/blurry inputs produce grainy outputs.
  Pre-process with an upscaler/denoiser (e.g. SEEDVR2) if needed.
* **Captioning — minimalist**: one short label per image, or just a single
  unique **trigger token** that doesn't collide with the tokenizer vocab,
  e.g. `<teach3r>` or `zztkperson`. Heavy descriptive captions inject
  unrelated features ("hat", "smiling") into your concept and cause
  feature bleed.
* **Folder layout** (Ostris / kohya style):

  ```
  dataset/
    teach3r/
      img_001.png
      img_001.txt    # contains: <teach3r>
      img_002.png
      img_002.txt    # contains: <teach3r>
      ...
  ```

### 4.2 Style / multi-concept LoRA (DiffSynth `metadata.csv` recipe)

The DiffSynth-Studio example used in the official HF blog uses a CSV:

```
dataset/
  metadata.csv
  images/
    00001.png
    00002.png
    ...
```

`metadata.csv`:

```csv
file_name,text
images/00001.png,"a red fox sitting on a mossy log, photoreal, soft rim light"
images/00002.png,"a red fox mid-jump over a stream, photoreal, golden hour"
...
```

* **Count**: a few hundred to a few thousand for a style.
* **Captions**: full natural-language prompts (one or two sentences),
  describing the *content* but consistently using the same words for the
  *style*. Z-Image is bilingual (EN/中文) — you can caption in either.
* **Resolution**: keep `max_pixels=1048576` (1024²) unless you have headroom.

### 4.3 Things that ruin a Z-Image Turbo dataset

* Mixed resolutions where some images are <1024 on the short edge (the
  model was distilled at 1024; sub-1024 inputs degrade fidelity).
* Per-image, hyper-detailed captions for an *identity* LoRA — the model
  memorizes the caption distribution instead of the face.
* Heavy JPEG compression / upscaled-from-512 inputs — Z-Image-Turbo is
  honest about input quality.
* CFG / aesthetic prompts ("masterpiece, best quality") in captions; Turbo
  uses `guidance_scale=0` and these tokens just become noise.

---

## 5. A concrete recipe — Scheme 4, LoRA with the Ostris adapter

This is the path most people actually take. It works on a single 24 GB GPU
and preserves 8-step inference.

### 5.1 Environment

```bash
# Diffusers from main is required for ZImagePipeline support
pip install -U "git+https://github.com/huggingface/diffusers"
pip install -U transformers accelerate peft safetensors
pip install bitsandbytes      # for 8-bit AdamW
# Trainer:
git clone https://github.com/ostris/ai-toolkit && cd ai-toolkit && pip install -r requirements.txt
# (or DiffSynth-Studio if you want the official examples)
```

Pull the training adapter:

```bash
huggingface-cli download ostris/zimage_turbo_training_adapter \
    zimage_turbo_training_adapter_v2.safetensors \
    --local-dir ./weights/z-image-turbo
```

### 5.2 ai-toolkit config (Z-Image Turbo, single-concept LoRA)

`configs/teach3r.yaml`:

```yaml
job: extension
config:
  name: teach3r
  process:
    - type: sd_trainer
      training_folder: ./output
      device: cuda:0
      trigger_word: "<teach3r>"

      model:
        name_or_path: "Tongyi-MAI/Z-Image-Turbo"
        is_z_image: true
        dtype: fp16
        quantize: false            # set true on <16 GB; uses NF4
        low_vram: false            # set true on <16 GB

      # The all-important piece: load the training adapter so we
      # don't smash the distilled 8-step trajectory.
      adapter:
        path: ./weights/z-image-turbo/zimage_turbo_training_adapter_v2.safetensors

      network:
        type: lora
        linear: 16                 # rank
        linear_alpha: 16
        # Target the DiT attention + MLP projections
        target_modules: ["to_q","to_k","to_v","to_out.0","w1","w2","w3"]

      train:
        batch_size: 1
        steps: 3000
        gradient_accumulation_steps: 1
        gradient_checkpointing: true
        noise_scheduler: flowmatch
        timestep_type: sigmoid
        optimizer: adamw8bit
        lr: 0.00025
        weight_decay: 0.0001
        save_every: 500
        sample_every: 250
        max_step_saves_to_keep: 6

      datasets:
        - folder_path: ./dataset/teach3r
          caption_ext: txt
          resolution: [1024]
          shuffle_tokens: false
          cache_latents_to_disk: true

      sample:
        seed: 42
        sampler: flowmatch
        sample_steps: 9            # 8 DiT forwards — verify Turbo path
        guidance_scale: 0.0
        width: 1024
        height: 1024
        prompts:
          - "<teach3r>, studio portrait, soft light"
          - "<teach3r> on a basketball court, golden hour, 35mm"
```

Run it:

```bash
python run.py configs/teach3r.yaml
```

Expected: 15–22 min on a 5090, ~1 h on a 3090, ~2–3 h on a 3060.

### 5.3 DiffSynth-Studio equivalent (the official HF blog command)

For style/multi-concept work with a CSV-driven dataset:

```bash
accelerate launch examples/z_image/model_training/train.py \
  --dataset_base_path data/example_image_dataset \
  --dataset_metadata_path data/example_image_dataset/metadata.csv \
  --max_pixels 1048576 \
  --dataset_repeat 50 \
  --model_id_with_origin_paths \
    "Tongyi-MAI/Z-Image-Turbo:transformer/*.safetensors,\
     Tongyi-MAI/Z-Image-Turbo:text_encoder/*.safetensors,\
     Tongyi-MAI/Z-Image-Turbo:vae/diffusion_pytorch_model.safetensors" \
  --learning_rate 1e-4 \
  --num_epochs 5 \
  --remove_prefix_in_ckpt "pipe.dit." \
  --output_path ./models/train/Z-Image-Turbo_lora \
  --lora_base_model dit \
  --lora_target_modules "to_q,to_k,to_v,to_out.0,w1,w2,w3" \
  --lora_rank 32 \
  --use_gradient_checkpointing \
  --dataset_num_workers 8
```

Five epochs × 50 repeats over a small dataset ≈ 250 optimizer steps. For
real style transfer, scale `num_epochs` until you reach a few thousand
optimizer steps.

---

## 6. Inference with your trained LoRA

```python
import torch
from diffusers import ZImagePipeline

pipe = ZImagePipeline.from_pretrained(
    "Tongyi-MAI/Z-Image-Turbo",
    torch_dtype=torch.bfloat16,
).to("cuda")

# Your trained LoRA
pipe.load_lora_weights(
    "./output/teach3r/teach3r_000003000.safetensors",
    adapter_name="teach3r",
)

# Scheme 4: also load a DistillPatch / training adapter to restore the
# 8-step trajectory at inference. (Skip for Scheme 1 — but then use
# num_inference_steps=30, guidance_scale=2.0.)
pipe.load_lora_weights(
    "./weights/z-image-turbo/zimage_turbo_training_adapter_v2.safetensors",
    adapter_name="distill_patch",
)
pipe.set_adapters(["teach3r", "distill_patch"], adapter_weights=[0.9, 1.0])

img = pipe(
    prompt="<teach3r>, school teacher shooting a basketball, smiling, 35mm",
    height=1024, width=1024,
    num_inference_steps=9,         # 8 DiT forwards
    guidance_scale=0.0,            # Turbo path
    generator=torch.Generator("cuda").manual_seed(42),
).images[0]
img.save("out.png")
```

If the result is **smooth/plasticky or washed out at 9 steps but fine at 30**,
your training broke the trajectory and you forgot the patch LoRA.

---

## 7. Hyperparameter cheat-sheet

| Knob                 | Identity LoRA (5–60 imgs) | Style LoRA (100s–1000s)  |
|----------------------|---------------------------|--------------------------|
| Rank / alpha         | 8–16                      | 16–32                    |
| LR                   | 1e-4 → 2.5e-4             | 1e-4                     |
| Optimizer            | AdamW8bit, wd 1e-4        | AdamW                    |
| Scheduler            | flowmatch / sigmoid       | flowmatch / sigmoid      |
| Steps                | 2.5k–3k (up to 5k)        | enough for ~5 epochs × dataset_repeat 50 |
| Batch size           | 1 (2 if VRAM allows)      | 1–4                      |
| Resolution           | 1024²                     | 1024² (max_pixels 1M)    |
| Gradient ckpt        | on                        | on                       |
| Save every           | 500                       | 500–1000                 |
| Sample every         | 250 (fixed seeds)         | 500                      |

Watch the sample images at 250-step intervals; **stop training the moment the
concept stabilizes** — Turbo is more prone to overfitting than full Z-Image.

---

## 8. Gotchas specific to Turbo

* `guidance_scale` must be **0.0** at inference; CFG was distilled into the
  weights. Non-zero CFG produces oversaturated junk.
* `num_inference_steps=9` is correct for "8 DiT forwards" with the current
  scheduler — not a typo. Some forks expose this as `steps=8`.
* Use `bfloat16` for inference, `float16` for training. Mixing them OOMs.
* If you trained without the adapter and your samples look bad at 9 steps,
  don't retrain — first try loading `zimage_turbo_training_adapter_v2`
  (or `Z-Image-Turbo-DistillPatch`) at inference. Often that's the whole fix.
* Latest `diffusers` from `main` is required; the pip release lags Z-Image
  support.
* `Z-Image-De-Turbo` exists as a community "un-distilled" variant for people
  who want to train against a 50-step trajectory from a Turbo init — niche,
  but useful if Scheme 1 results disappoint.

---

## 9. TL;DR

* **5–60 images** at 1024², minimalist captions / single trigger token, is
  enough for a character LoRA.
* **~3 000 steps**, rank 16, LR 1e-4–2.5e-4, AdamW8bit, flowmatch scheduler.
* **24 GB GPU** comfortably; **12 GB** doable with int8 + rank 8.
* Train a **normal LoRA** *plus* load `zimage_turbo_training_adapter_v2`
  (and/or the DistillPatch LoRA) at inference. That's Scheme 4 — the
  recommended path.
* Inference stays at `steps=9, guidance_scale=0.0, bf16`.

---

## Sources

* [Tongyi-MAI/Z-Image-Turbo — model card (HF)](https://huggingface.co/Tongyi-MAI/Z-Image-Turbo)
* [Training Strategies of Z-Image-Turbo — kelseye, HF blog](https://huggingface.co/blog/kelseye/training-strategies-of-z-image-turbo)
* [Engineering Notes: Training a LoRA for Z-Image Turbo with the Ostris AI Toolkit — HF blog](https://huggingface.co/blog/content-and-code/training-a-lora-for-z-image-turbo)
* [Z-Image-Turbo LoRA Training Setup – Full Precision + Adapter v2 — Civitai](https://civitai.com/articles/23863/z-image-turbo-lora-training-setup-full-precision-adapter-v2-massive-quality-jump)
* [Z Image Trainer: LoRA Training for Z-Image Turbo — fal.ai](https://fal.ai/models/fal-ai/z-image-trainer)
* [LoRA Training and fine-tuning? — Z-Image-Turbo discussion #11](https://huggingface.co/Tongyi-MAI/Z-Image-Turbo/discussions/11)
* [Training Z-Image-Turbo LoRA using 12G VRAM — Tongyi-MAI/Z-Image issue #36](https://github.com/Tongyi-MAI/Z-Image/issues/36)
* [Best Practice for Z-Image Base vs Turbo LoRA Training — discussion #18](https://huggingface.co/Tongyi-MAI/Z-Image/discussions/18)
* Decoupled-DMD paper: arXiv:2511.22677. Z-Image paper: arXiv:2511.22699.

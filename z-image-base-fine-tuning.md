# Fine-tuning Z-Image (base, non-Turbo)

A practical guide for fine-tuning the **full Z-Image** foundation model from
Tongyi-MAI — the 50-step, non-distilled sibling of Z-Image-Turbo. This is the
checkpoint Tongyi officially labels as **"Easy"** for fine-tuning, with full
support for LoRA, full SFT, distillation training, and ControlNet.

If you specifically want to keep 8-step inference, see the companion file
`z-image-turbo-post-training.md`. If you want the cleanest fine-tuning
experience — with CFG, negative prompts, and arbitrary samplers — fine-tune
the base, then optionally distill or apply your LoRA to Turbo at inference.

---

## 1. What "Z-Image (base)" is

| Piece                  | Value                                                                |
|------------------------|----------------------------------------------------------------------|
| Architecture           | Single-stream DiT (text + visual semantic + VAE tokens concatenated) |
| Parameters             | ~6 B in the DiT (same backbone as Turbo)                             |
| Training objective     | Flow-matching, **not** distilled                                     |
| Inference              | 28–50 steps, `guidance_scale=3.0–5.0`, supports negative prompts     |
| Recommended dtype      | **bf16** (FP16 produces visibly worse results on the base model)     |
| Resolution range       | 512² to 2048², arbitrary aspect ratios                               |
| VRAM for inference     | ~16 GB bf16; 8–10 GB with int4/NF4                                   |
| License                | Apache-2.0                                                           |
| Variants               | `Z-Image`, `Z-Image-Omni-Base` (multimodal/edit), `Z-Image-Turbo`    |

**Why you'd choose base over Turbo for training:**

* **No distilled trajectory to break.** You can do plain SFT or LoRA without
  worrying about DistillPatch / training adapters.
* **CFG works**, so you can use negative prompts during validation.
* **Community result**: LoRAs trained on **Z-Image base** transfer to
  Z-Image-Turbo at inference better than LoRAs trained on Turbo do (people
  report markedly better identity preservation), though you may need to push
  LoRA strength to ~2.0–2.5 when applying a base-trained LoRA to Turbo.

The cost of choosing base is that **inference is ~4–6× slower** (50 steps vs
8) and you give up Turbo's sub-second latency on H800.

---

## 2. The training options

Unlike Turbo, base Z-Image has no "schemes 1–4." There are just three real
choices, and they map onto budget:

| Choice                | Touches all weights? | VRAM @1024² (24 GB realistic?) | Cost                          |
|-----------------------|----------------------|--------------------------------|-------------------------------|
| **LoRA SFT**          | No (low-rank adapters) | ✅ Yes                       | Cheap. Default.               |
| **Full SFT**          | Yes (every DiT param)  | ❌ Needs 80 GB-class GPUs     | 10–100× LoRA.                 |
| **Distillation**      | Either                 | Needs Z-Image **and** Turbo loaded | Use to *make your own Turbo* from your fine-tune. |

ControlNet / structural conditioning training is also supported via
DiffSynth-Studio; that's outside the scope of this guide but uses the
same training script with a different head.

---

## 3. Compute required

### LoRA SFT @ 1024², rank 32

| GPU            | VRAM | Setup                                            | Time @ 3k steps   | Notes                                                |
|----------------|------|--------------------------------------------------|-------------------|------------------------------------------------------|
| RTX 5090       | 32 GB| bf16, rank 32, batch 1, no quant                 | ~25–35 min        | Comfortable.                                         |
| RTX 4090       | 24 GB| bf16, rank 32, batch 1, grad ckpt                | ~60–90 min        | Sweet spot for LoRA.                                 |
| RTX 3090       | 24 GB| bf16, rank 32, batch 1, grad ckpt                | ~90–120 min       | Bf16 throughput is lower than 40-series.             |
| RTX 3060 12 GB | 12 GB| int8 base + rank 16 + grad ckpt + low-VRAM mode  | ~4–6 h            | Possible but slow; cache latents to disk.            |
| RTX 3060 8 GB  | 8 GB | NF4 base + rank 8 + grad ckpt + grad accum 8     | ~6–10 h           | Workable; OOMs on aggressive augmentations.          |

Bf16 base costs roughly ~1.3–1.5× the time of fp16 Turbo training at the
same rank, both because each training step still touches the full 6 B DiT
(LoRA doesn't change that) and because base training doesn't get to use the
training-adapter shortcut.

### Full SFT

Realistic only on 80 GB-class hardware:

* **1× H100 / A100 80 GB**: bf16, batch 1–2 at 1024², grad ckpt on, ZeRO-2
  via DeepSpeed/`accelerate`. Roughly **10–20 K steps** for a several-thousand
  image style dataset.
* **8× H100**: similar wall-clock as 1× H100 for the same per-GPU batch
  thanks to data parallel; lets you use larger global batch and reach
  convergence in fewer epochs.
* No official Tongyi pre-training recipe has been published; the numbers
  above are extrapolated from the DiffSynth-Studio `full_training` script
  defaults.

### Distillation (your-base → your-Turbo)

Effectively 2× LoRA SFT compute, since you must hold the teacher (your
fine-tuned 50-step model) and the student (an 8-NFE student) in memory at
the same time. Budget **1–2 80 GB GPUs**.

---

## 4. Dataset: how many images, and how to annotate them

Base Z-Image is more forgiving than Turbo in two ways: it tolerates a wider
caption style, and it doesn't punish you for input-resolution mismatches as
hard. You still want quality data.

### 4.1 Single-concept / character LoRA

* **Count**: 15–80 images. The classic "70–80 high-quality photos" recipe
  from the community gives you robust skin texture and pose variety. 9–15
  images can imprint a face but won't generalize across angles.
* **Resolution**: **1024² is the safe default.** Z-Image was trained
  natively at 1024 and degrades less than Turbo at non-square aspect ratios.
* **Captions — short tag**: Minimalist captions still work best for *identity*
  LoRAs. A single distinctive trigger token (e.g. `<zztkperson>`) plus, at
  most, a class word ("man", "woman", "dog") per image.

### 4.2 Style or multi-concept LoRA

* **Count**: 200 – 5 000 images for a coherent style. 10 K+ if you want a
  real domain shift (e.g. medical imagery).
* **Captions — natural language**: full sentences describing *content* but
  using a consistent style anchor. The DiffSynth recipe is the standard:

  ```csv
  file_name,text
  images/0001.png,"<myStyleTag>, a fox in a snowy forest, painterly oil"
  images/0002.png,"<myStyleTag>, a portrait of a child, painterly oil"
  ```

  Z-Image is bilingual (EN / 中文) — either works, but stay consistent
  within a dataset to avoid encoder drift.

### 4.3 Differences from Turbo dataset prep

* **OK to vary resolution**: dynamic-resolution training is supported by
  DiffSynth's Z-Image script (`--height`/`--width` accept lists). Bucket
  by aspect ratio.
* **Negative prompts can be validated**: `negative_prompt` works at
  inference, so include diversity-checking prompts ("low quality, blurry")
  in your validation set.
* **Avoid "masterpiece"/aesthetic spam** in captions. The base model was
  trained on clean captions; injecting tag-soup gives you tag-soup back.

### 4.4 Universal data-quality rules

* No <1024-px short edge.
* No JPEG-of-JPEG re-encodes. Pre-process with a real denoiser (e.g.
  SEEDVR2) if you must use phone photos.
* For identity LoRAs: consistent lighting per shoot, varied lighting
  across shoots. The model overfits faces under one light source very fast.

---

## 5. A concrete recipe — LoRA SFT with DiffSynth-Studio

DiffSynth-Studio is what Tongyi themselves point at for Z-Image training.
The script is `examples/z_image/model_training/train.py`.

### 5.1 Environment

```bash
pip install -U "git+https://github.com/huggingface/diffusers"
pip install -U transformers accelerate peft safetensors bitsandbytes
git clone https://github.com/modelscope/DiffSynth-Studio
cd DiffSynth-Studio
pip install -e .
```

### 5.2 Dataset

```
data/my_dataset/
  metadata.csv
  images/
    0001.png
    0002.png
    ...
```

`metadata.csv` (same schema as the Turbo example, but you can be more verbose):

```csv
file_name,text
images/0001.png,"<myStyleTag>, a red fox on a mossy log, photoreal, soft rim light"
images/0002.png,"<myStyleTag>, a red fox mid-jump over a stream, golden hour"
```

### 5.3 Launch command (LoRA, base Z-Image)

```bash
accelerate launch examples/z_image/model_training/train.py \
  --dataset_base_path data/my_dataset \
  --dataset_metadata_path data/my_dataset/metadata.csv \
  --max_pixels 1048576 \
  --dataset_repeat 50 \
  --model_id_with_origin_paths \
    "Tongyi-MAI/Z-Image:transformer/*.safetensors,\
     Tongyi-MAI/Z-Image:text_encoder/*.safetensors,\
     Tongyi-MAI/Z-Image:vae/diffusion_pytorch_model.safetensors" \
  --learning_rate 1e-4 \
  --num_epochs 5 \
  --remove_prefix_in_ckpt "pipe.dit." \
  --output_path ./models/train/Z-Image_lora \
  --lora_base_model dit \
  --lora_target_modules "to_q,to_k,to_v,to_out.0,w1,w2,w3" \
  --lora_rank 32 \
  --use_gradient_checkpointing \
  --dataset_num_workers 8 \
  --mixed_precision bf16
```

The only material changes from the Turbo command are:

* `Tongyi-MAI/Z-Image` (base) instead of `Tongyi-MAI/Z-Image-Turbo`.
* `--mixed_precision bf16` (the community-tested choice for base).
* **No training adapter / DistillPatch** anywhere in the pipeline.

5 epochs × `dataset_repeat 50` over a small dataset gives you ~250 optimizer
steps; bump `num_epochs` until you reach 3 K–10 K steps for a real style.

### 5.4 Full SFT variant

Same script, drop the LoRA flags and add `--full_training`:

```bash
accelerate launch \
  --multi_gpu --num_processes 8 \
  examples/z_image/model_training/train.py \
  --model_id_with_origin_paths "Tongyi-MAI/Z-Image:..." \
  --full_training \
  --learning_rate 5e-6 \
  --num_epochs 20 \
  --use_gradient_checkpointing \
  --use_zero2 \
  --mixed_precision bf16 \
  --max_pixels 1048576 \
  --dataset_repeat 1
```

* Drop the LR by ~20× vs. LoRA — full FT is much more sensitive.
* ZeRO-2 (DeepSpeed) keeps a 6 B DiT inside 80 GB per rank.
* You probably want `--dataset_repeat 1` and many real epochs, not
  artificially repeated steps, so loss curves stay interpretable.

### 5.5 AI-Toolkit alternative (single GPU, friendlier UX)

If you prefer Ostris ai-toolkit, the YAML is almost identical to the Turbo
one in `z-image-turbo-post-training.md`, with two changes:

```yaml
model:
  name_or_path: "Tongyi-MAI/Z-Image"     # not -Turbo
  is_z_image: true
  dtype: bf16                            # not fp16
  quantize: false
  low_vram: false

# REMOVE the `adapter:` block entirely.
# No training adapter is needed for base Z-Image.

train:
  lr: 0.0001
  steps: 3000
  optimizer: adamw8bit
  weight_decay: 0.0001
  noise_scheduler: flowmatch
  timestep_type: sigmoid
  gradient_checkpointing: true

network:
  type: lora
  linear: 32                              # base tolerates higher rank
  linear_alpha: 32

sample:
  sample_steps: 30
  guidance_scale: 4.0                     # CFG works on base!
  negative_prompt: "low quality, blurry, deformed"
```

Note the inference-side knobs that are *only available on base*:
`guidance_scale` ≠ 0 and `negative_prompt`.

---

## 6. Inference with your trained LoRA

### 6.1 On the base model (recommended for evaluation)

```python
import torch
from diffusers import ZImagePipeline

pipe = ZImagePipeline.from_pretrained(
    "Tongyi-MAI/Z-Image",
    torch_dtype=torch.bfloat16,
).to("cuda")

pipe.load_lora_weights(
    "./models/train/Z-Image_lora/lora.safetensors",
    adapter_name="myStyle",
)
pipe.set_adapters(["myStyle"], adapter_weights=[1.0])

img = pipe(
    prompt="<myStyleTag>, a red fox on a snowy log, photoreal",
    negative_prompt="low quality, blurry, deformed",
    height=1024, width=1024,
    num_inference_steps=30,
    guidance_scale=4.0,
    generator=torch.Generator("cuda").manual_seed(42),
).images[0]
img.save("base.png")
```

### 6.2 Same LoRA, generated on Turbo (production speed)

This is the workflow people actually deploy:

```python
import torch
from diffusers import ZImagePipeline

pipe = ZImagePipeline.from_pretrained(
    "Tongyi-MAI/Z-Image-Turbo",
    torch_dtype=torch.bfloat16,
).to("cuda")

# Base-trained LoRA tends to be "too weak" on Turbo at 1.0 —
# push the weight to 2.0–2.5.
pipe.load_lora_weights(
    "./models/train/Z-Image_lora/lora.safetensors",
    adapter_name="myStyle",
)
pipe.set_adapters(["myStyle"], adapter_weights=[2.0])

img = pipe(
    prompt="<myStyleTag>, a red fox on a snowy log, photoreal",
    height=1024, width=1024,
    num_inference_steps=9,
    guidance_scale=0.0,         # Turbo path — CFG disabled
    generator=torch.Generator("cuda").manual_seed(42),
).images[0]
img.save("turbo.png")
```

This is the "train on Base → infer on Turbo" pattern, and in community
A/B tests it beats training on Turbo directly for identity LoRAs. You may
also load `ostris/zimage_turbo_training_adapter_v2` alongside if your
base LoRA visibly disturbs Turbo's trajectory, but it's usually not needed.

---

## 7. Hyperparameter cheat-sheet

| Knob                 | Identity LoRA (15–80 imgs)| Style LoRA (200–5 K)     | Full SFT             |
|----------------------|---------------------------|--------------------------|----------------------|
| Rank / alpha         | 16–32                     | 32–64                    | n/a                  |
| LR                   | 1e-4                      | 1e-4 → 2e-4              | 5e-6 → 1e-5          |
| Optimizer            | AdamW8bit, wd 1e-4        | AdamW8bit                | AdamW + warmup       |
| Scheduler            | flowmatch / sigmoid       | flowmatch / sigmoid      | flowmatch + cosine   |
| LR warmup            | 0–100 steps               | 50–200 steps             | 500–2 000 steps      |
| Steps                | 2.5 K–4 K                 | 5 K–20 K                 | tens of K            |
| Batch (per GPU)      | 1                         | 1–2                      | 1–2 + ZeRO-2         |
| Grad accumulation    | 1                         | 1–4                      | as needed for budget |
| Resolution           | 1024² fixed               | 1024² bucketed           | 1024² bucketed       |
| Precision (train)    | **bf16**                  | **bf16**                 | bf16                 |
| Gradient checkpoint  | on                        | on                       | on (mandatory)       |
| Save every           | 500                       | 1 000                    | 2 000                |
| Sample every         | 250 (fixed seeds)         | 500                      | 1 000                |
| Inference steps      | 30                        | 30–50                    | 30–50                |
| Inference CFG        | 4.0                       | 3.0–5.0                  | 3.0–5.0              |

---

## 8. Gotchas specific to base

* **Train in bf16, not fp16.** Multiple users report identity / color
  drift when training base in fp16 and inferring in bf16 (or vice versa).
  Pick bf16 and stay there.
* **CFG is required at inference.** `guidance_scale=0` on base looks like
  fog. Use 3–5.
* **More steps to converge.** Plan for 3 K–10 K steps on a real style;
  Turbo often finishes around 2 K because its trajectory is already
  collapsed.
* **Bigger models from a LoRA**. Ranks 32–64 are fine on base; on Turbo
  they wreck the trajectory. Use the headroom.
* **LoRA strength when porting to Turbo**: scale to 2.0–2.5. A 1.0-weight
  base LoRA looks too subtle under 8-NFE inference.
* **Background faces** in base outputs are notoriously rough — this is a
  known model limitation, not something more training fixes. Use a tight
  negative prompt or a face-restore post-step.
* **Diffusers from `main`** is still required (the pip release lags).

---

## 9. TL;DR

* Z-Image base is the **non-distilled 6 B DiT**. Fine-tune it in **bf16**
  with **rank 32 LoRA**, **LR 1e-4**, **flowmatch** scheduler, **~3 K steps**.
* Inference: **28–50 steps, CFG 3–5, negative prompts allowed.**
* **No DistillPatch / training adapter** is needed — that machinery only
  exists to protect Turbo's 8-step path.
* For best quality + best latency: **train on base, deploy on Turbo with
  LoRA weight ~2.0–2.5** (and `steps=9, guidance_scale=0` at inference).
* Compute floor for LoRA: ~12 GB VRAM with int8 + rank 16; comfortable
  at 24 GB; fast at 32 GB. Full SFT realistically needs an 80 GB GPU.

---

## Sources

* [Tongyi-MAI/Z-Image — model card (HF)](https://huggingface.co/Tongyi-MAI/Z-Image)
* [Tongyi-MAI/Z-Image-Turbo — model card (HF)](https://huggingface.co/Tongyi-MAI/Z-Image-Turbo)
* [DiffSynth-Studio — Z-Image model docs](https://github.com/modelscope/DiffSynth-Studio/blob/main/docs/en/Model_Details/Z-Image.md)
* [Training Strategies of Z-Image-Turbo — kelseye, HF blog](https://huggingface.co/blog/kelseye/training-strategies-of-z-image-turbo)
* [Best Practice for Z-Image Base vs Turbo LoRA Training — Tongyi-MAI/Z-Image discussion #18](https://huggingface.co/Tongyi-MAI/Z-Image/discussions/18)
* [LoRA Fine-tuning Results in Visual Artifacts — Tongyi-MAI/Z-Image issue #138](https://github.com/Tongyi-MAI/Z-Image/issues/138)
* [Fine-Tune Z-Image Base with AI Toolkit — Apatero blog](https://www.apatero.com/blog/z-image-base-ai-toolkit-fine-tuning)
* [How to Train Better LoRA Models with Z-Image — zimage.run](https://zimage.run/blog/best-practices-training-lora-models-z-image)
* [Tongyi-MAI/Z-Image — GitHub repo](https://github.com/Tongyi-MAI/Z-Image)
* Z-Image paper: arXiv:2511.22699. Decoupled-DMD paper: arXiv:2511.22677.

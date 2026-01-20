# Hugo Migration Plan for sledgeworx.io

## Executive Summary

This document outlines a plan to migrate sledgeworx.io from WordPress to Hugo, a static site generator. The migration will preserve all essential functionality while eliminating unnecessary features like the mailing list integration.

---

## Current Site Analysis

### Platform
- **Current CMS**: WordPress
- **Hosting**: Standard WordPress hosting
- **Key Integrations**: MailerLite (to be removed), WP Statistics, WordPress comments

### Content Inventory

| Content Type | Estimated Count | Notes |
|-------------|----------------|-------|
| Blog Posts | ~150+ | 15 pages of posts in Software Engineering category alone |
| Guides | 15 | Curated technical guides |
| Static Pages | 4-5 | About, SledgeConf, Handbook, etc. |
| Categories | 8+ | Software Engineering, Guide, Product, etc. |
| Tags | 20+ | agile, estimates, cloud, migration, etc. |
| Archives | 2018-2025 | Monthly archives spanning 7+ years |

### Current Features

| Feature | Status | Hugo Support |
|---------|--------|--------------|
| Blog posts with dates | Active | Native |
| Categories & Tags | Active | Native (taxonomies) |
| Archives (monthly/yearly) | Active | Native |
| Search | Active | Requires solution |
| Comments | Active | Third-party needed |
| Email subscription | Active | **NOT MIGRATING** |
| Responsive design | Active | Theme-dependent |
| Social sharing | Active | Theme/shortcode |
| Recent posts widget | Active | Native |
| Related posts | Active | Native |

---

## Required Hugo Features

### 1. Content Types (Archetypes)

```
content/
├── posts/           # Blog posts
├── guides/          # Technical guides (separate section)
├── pages/           # Static pages
│   ├── about.md
│   ├── sledgeconf.md
│   └── handbook.md
```

### 2. Taxonomies

```toml
# hugo.toml
[taxonomies]
  category = "categories"
  tag = "tags"
```

**Required Categories:**
- Software Engineering
- Software Industry
- Guide
- Product
- Programming
- AI/Cybersecurity (newer posts)

### 3. Navigation Structure

**Main Menu:**
- About
- Contact
- SledgeConf
- Handbook (Books)
- Guides
- ~~Consulting~~ (404 - verify if needed)

### 4. Sidebar Widgets (to implement in theme/partials)

- Recent Posts (5 most recent)
- Categories list
- Archives (monthly)
- ~~Email subscription~~ (NOT NEEDED)

### 5. Search Functionality

**Options:**
1. **Pagefind** (Recommended) - Static search, no external dependencies
2. **Fuse.js** - Client-side fuzzy search with JSON index
3. **Algolia** - External service, more powerful but adds complexity

**Recommendation:** Pagefind - easy to integrate, fast, privacy-friendly

### 6. Comments System

**Options:**
1. **Giscus** (Recommended) - GitHub Discussions-based, free
2. **Disqus** - Popular but has ads/tracking
3. **Utterances** - GitHub Issues-based
4. **None** - Remove comments entirely

**Recommendation:** Giscus or remove comments (many static blogs thrive without them)

---

## Theme Requirements

### Essential Features
- Responsive/mobile-friendly
- Blog-focused layout
- Sidebar support
- Category/tag pages
- Archive pages
- Clean typography for technical content
- Code syntax highlighting
- Fast loading

### Recommended Themes

| Theme | Pros | Cons |
|-------|------|------|
| **PaperMod** | Fast, clean, popular, good defaults | May need sidebar customization |
| **Stack** | Built-in sidebar, search, good for tech blogs | More opinionated design |
| **Blowfish** | Modern, feature-rich, Tailwind-based | Larger, more complex |
| **Congo** | Clean, fast, good documentation | Minimalist (may need additions) |

**Recommendation:** Start with **PaperMod** or **Stack** - both are well-maintained and suitable for technical blogs.

---

## Migration Steps

### Phase 1: Setup & Configuration

1. **Initialize Hugo site**
   ```bash
   hugo new site sledgeworx
   cd sledgeworx
   ```

2. **Install theme** (example with PaperMod)
   ```bash
   git submodule add https://github.com/adityatelange/hugo-PaperMod themes/PaperMod
   ```

3. **Configure hugo.toml**
   - Site metadata (title, description, baseURL)
   - Taxonomies (categories, tags)
   - Menu structure
   - Theme settings
   - Permalink structure to match existing URLs (important for SEO)

### Phase 2: Content Export from WordPress

1. **Export WordPress content**
   - Use WordPress export (Tools > Export > All content)
   - Download XML file

2. **Convert to Hugo format**
   - Use `wordpress-to-hugo-exporter` plugin, OR
   - Use `blog2md` tool, OR
   - Use `wp2hugo` CLI tool

   ```bash
   # Example with wp2hugo
   wp2hugo --source wordpress-export.xml --output content/
   ```

3. **Post-conversion cleanup**
   - Fix image paths
   - Convert shortcodes to Hugo equivalents
   - Verify front matter (date, categories, tags)
   - Fix internal links

### Phase 3: Content Organization

1. **Organize posts by type**
   ```
   content/
   ├── posts/
   │   └── 2024/
   │       └── my-post.md
   ├── guides/
   │   └── code-review-handbook.md
   └── about.md
   ```

2. **Create front matter template**
   ```yaml
   ---
   title: "Post Title"
   date: 2024-01-15
   categories: ["Software Engineering"]
   tags: ["agile", "estimation"]
   description: "Brief description for SEO"
   draft: false
   ---
   ```

3. **Set up Guides as a separate section**
   - Create `content/guides/_index.md` with list template
   - Move guide posts to this section

### Phase 4: Theme Customization

1. **Create custom layouts as needed**
   - `layouts/guides/list.html` - Guides listing page
   - `layouts/partials/sidebar.html` - Sidebar widgets

2. **Implement sidebar**
   - Recent posts partial
   - Categories list partial
   - Archives partial

3. **Style adjustments**
   - Match branding (logo, colors)
   - Typography for code blocks
   - Responsive breakpoints

### Phase 5: Additional Features

1. **Search implementation**
   ```bash
   # Add Pagefind after build
   npx pagefind --site public
   ```

2. **Comments (if keeping)**
   - Set up Giscus with GitHub repository
   - Add to single post template

3. **Analytics** (optional)
   - Add Plausible, Fathom, or Google Analytics
   - Configure in hugo.toml

### Phase 6: URL Preservation (SEO Critical)

1. **Match WordPress permalink structure**
   ```toml
   # hugo.toml
   [permalinks]
     posts = "/:slug/"
   ```

2. **Create redirects for any changed URLs**
   - Use `aliases` in front matter, OR
   - Configure at hosting level (Netlify `_redirects`, etc.)

3. **Verify all old URLs work**
   - Test category pages: `/category/software-engineering/`
   - Test tag pages: `/tag/agile/`
   - Test archive pages: `/2024/01/`

### Phase 7: Deployment

**Recommended Hosting Options:**

| Platform | Pros | Cons |
|----------|------|------|
| **Netlify** | Free tier, easy deploy, good DX | Minor lock-in |
| **Cloudflare Pages** | Very fast, free, good security | Less mature |
| **GitHub Pages** | Free, simple | Custom domain HTTPS setup |
| **Vercel** | Fast, good DX | Primarily for Next.js |

**Deployment workflow:**
1. Push to GitHub
2. Netlify/Cloudflare auto-builds and deploys
3. Configure custom domain
4. Set up SSL certificate (usually automatic)

---

## Content Migration Checklist

- [ ] Export WordPress XML
- [ ] Convert posts to Markdown
- [ ] Verify all posts converted (~150+)
- [ ] Convert 15 guides
- [ ] Migrate About page
- [ ] Migrate SledgeConf page
- [ ] Migrate Handbook page
- [ ] Download and organize all images
- [ ] Fix image references in content
- [ ] Verify categories preserved
- [ ] Verify tags preserved
- [ ] Test internal links
- [ ] Create 301 redirects for changed URLs
- [ ] Test on staging before launch

---

## Recommended Configuration

### Sample hugo.toml

```toml
baseURL = "https://www.sledgeworx.io/"
languageCode = "en-us"
title = "Sledgeworx Software"
theme = "PaperMod"

[params]
  description = "Software Engineering Insights by Nick Sledgianowski"
  author = "Nick Sledgianowski"
  ShowReadingTime = true
  ShowShareButtons = true
  ShowPostNavLinks = true
  ShowBreadCrumbs = true
  ShowCodeCopyButtons = true

[params.homeInfoParams]
  Title = "Sledgeworx Software"
  Content = "Blog posts, guides, and insights on software engineering"

[taxonomies]
  category = "categories"
  tag = "tags"

[permalinks]
  posts = "/:slug/"

[[menu.main]]
  name = "About"
  url = "/about/"
  weight = 10

[[menu.main]]
  name = "Guides"
  url = "/guides/"
  weight = 20

[[menu.main]]
  name = "SledgeConf"
  url = "/sledgeconf/"
  weight = 30

[[menu.main]]
  name = "Handbook"
  url = "/getting-into-software-handbook/"
  weight = 40

[markup]
  [markup.highlight]
    style = "github-dark"
    lineNos = false

[outputs]
  home = ["HTML", "RSS", "JSON"]  # JSON for search
```

---

## Removed Features (Per Requirements)

The following WordPress features will **NOT** be migrated:

1. **Email subscription/Mailing list** - MailerLite integration removed
2. **WordPress login** - Not applicable to static site
3. **WP Statistics** - Replace with privacy-friendly alternative if needed
4. **Dynamic comments** - Replace with static solution or remove

---

## Timeline Estimate

| Phase | Tasks |
|-------|-------|
| Phase 1 | Hugo setup, theme installation, basic config |
| Phase 2 | WordPress export and conversion |
| Phase 3 | Content organization and cleanup |
| Phase 4 | Theme customization and sidebar |
| Phase 5 | Search, comments, analytics |
| Phase 6 | URL testing and redirects |
| Phase 7 | Deployment and DNS cutover |

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Broken URLs | High (SEO) | Careful permalink matching, redirects |
| Missing content | High | Thorough conversion verification |
| Image path issues | Medium | Script to fix paths, manual review |
| Theme limitations | Medium | Choose flexible theme, plan customization |
| Search quality | Low | Pagefind is reliable, test thoroughly |

---

## Next Steps

1. **Confirm theme choice** - Review PaperMod and Stack demos
2. **Export WordPress content** - Generate XML export
3. **Set up development environment** - Install Hugo locally
4. **Begin Phase 1** - Initialize site and configure

---

## Resources

- [Hugo Documentation](https://gohugo.io/documentation/)
- [PaperMod Theme](https://github.com/adityatelange/hugo-PaperMod)
- [WordPress to Hugo Exporter](https://github.com/SchumacherFM/wordpress-to-hugo-exporter)
- [Pagefind Search](https://pagefind.app/)
- [Giscus Comments](https://giscus.app/)

# Lovable-to-Streamlit design mapping

The supplied Lovable project used TanStack Start, React, Tailwind CSS, Radix UI, and a custom design-token file. Streamlit cannot execute those React components directly, so the visual system was translated as follows.

| Lovable source concept | Integrated Streamlit implementation |
|---|---|
| `--cream` and `--cream-deep` | `.streamlit/config.toml` backgrounds and CSS variables |
| Coral and magenta palette | Primary theme color and `--warm-gradient` |
| `Fraunces` display font | CSS heading font |
| `Plus Jakarta Sans` | CSS body font |
| `bg-hero` radial background | App-level layered radial and linear gradients |
| Rounded Tailwind cards | Keyed `st.container` elements styled with CSS |
| Procedural `CharacterAvatar` SVG | Self-contained SVG character assets and inline SVG helpers |
| Hero phone mock | Static responsive HTML/CSS phone preview |
| React navigation | `st.navigation(..., position="top")` |
| Word-match and listening visual direction | Functional vocabulary, role-play, and sentence-expansion pages |
| Progress mockup | Live metrics, progress bars, bandit values, clustering output, and history |

## Core design tokens

```text
Cream:          #FFF9ED
Cream deep:     #FFEFDE
Coral:          #FF6A3D / #FF9173
Magenta:        #FF4F9A / #FF4DC4 / #F780BC
Ink:            #351C1C
Muted ink:      #795B56
Border:         #EDDAD0
Warm gradient:  #FF6A3D -> #FF4F9A -> #FF4DC4
```

The CSS is intentionally isolated in `assets/styles.css`. Update the variables at the top of that file to rebrand the whole app.

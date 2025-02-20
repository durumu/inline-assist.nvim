# inline-assist.nvim

A Neovim plugin implementing the AI inline assist feature from editors like Zed. Uses Claude Sonnet under the hood. Created for my own personal use, so it's not very configurable.

## How to use

Highlight some text in visual mode, then type `:InlineAssist Do some stuff`.

I recommend binding `:InlineAssist ` to <C-CR> or <M-CR>.

## Requirements

- Neovim, with a Python provider >= 3.10 (`:checkhealth provider`)
- `pip install anthropic` within your provider environment
- `ANTHROPIC_API_KEY` environment variable must be set

Here's how I've installed it, with lazy.nvim:

```lua
require("lazy").setup({
    -- my other plugins
    {
        "durumu/inline-assist.nvim",
        lazy = false,
        build = ":UpdateRemotePlugins",
        config = function() vim.keymap.set({ "n", "v" }, "<M-CR>", ":InlineAssist ") end,
    },
})
```

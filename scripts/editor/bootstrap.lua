-- Load the learner's unchanged config snapshot with container-only adaptations.
vim.opt.rtp:prepend(vim.fn.stdpath("data") .. "/lazy/lazy.nvim")
vim.opt.rtp:append(vim.fn.stdpath("data") .. "/lazy/nvim-treesitter/runtime")
local lazy = require("lazy")
local setup = lazy.setup
lazy.setup = function(opts)
  opts.checker = { enabled = false }
  opts.install = { missing = false }
  opts.rocks = { enabled = false }
  vim.list_extend(opts.spec, dofile("/opt/book-tools/editor/book_runtime.lua"))
  return setup(opts)
end
-- Kitty graphics must transmit bytes: the terminal cannot open container /tmp.
vim.env.SSH_TTY = "/dev/tty"
dofile(vim.fn.stdpath("config") .. "/init.lua")
-- Keep output readable without covering the notebook with long logs.
vim.g.molten_virt_text_max_lines = 8
vim.g.molten_output_win_max_height = 12
vim.g.molten_output_win_max_width = 100
-- Notebook buffers contain Markdown, so every save must use the converter.
vim.api.nvim_create_autocmd("BufReadPost", {
  pattern = "*.ipynb",
  callback = function(ev)
    vim.bo[ev.buf].buftype = "acwrite"
  end,
})
-- Molten saves outputs after Jupytext writes the source. Acknowledge that write
-- so the next save does not mistake our own output export for an external edit.
vim.api.nvim_create_autocmd("BufWritePost", {
  pattern = "*.ipynb",
  callback = function(ev)
    vim.schedule(function()
      if not vim.api.nvim_buf_is_valid(ev.buf) then return end
      local stat = vim.uv.fs_stat(vim.api.nvim_buf_get_name(ev.buf))
      if stat then vim.b[ev.buf].mtime = stat.mtime end
    end)
  end,
})

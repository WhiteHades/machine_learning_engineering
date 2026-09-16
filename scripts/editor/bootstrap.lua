-- Load the learner's unchanged config snapshot with container-only adaptations.
vim.opt.rtp:prepend(vim.fn.stdpath("data") .. "/lazy/lazy.nvim")
vim.opt.rtp:append(vim.fn.stdpath("data") .. "/lazy/nvim-treesitter/runtime")

-- The copied config enables web language extras that are unused in this book.
-- Keep them out before LazyVim evaluates their package paths.
local lazyvim_config = vim.fn.stdpath("config") .. "/lazyvim.json"
local lazyvim_book_config = vim.fn.stdpath("state") .. "/book-lazyvim.json"
if vim.fn.filereadable(lazyvim_config) == 1 then
  local ok, data = pcall(vim.json.decode, table.concat(vim.fn.readfile(lazyvim_config), "\n"))
  if ok and type(data) == "table" then
    data.extras = vim.tbl_filter(function(extra)
      return extra ~= "lazyvim.plugins.extras.lang.typescript"
        and extra ~= "lazyvim.plugins.extras.lang.vue"
    end, data.extras or {})
    vim.fn.writefile({ vim.json.encode(data) }, lazyvim_book_config)
    vim.g.lazyvim_json = lazyvim_book_config
  end
end

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

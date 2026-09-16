require("lazy").load({ plugins = { "nvim-treesitter" } })
local languages = require("lazy.core.plugin").values(require("lazy.core.config").plugins["nvim-treesitter"], "opts", false).ensure_installed
require("nvim-treesitter").install(languages):wait(300000)
vim.wait(300000, function()
  for _, lang in ipairs(languages) do
    local ok, loaded = pcall(vim.treesitter.language.add, lang)
    if not ok or not loaded then return false end
  end
  return true
end, 100)
for _, lang in ipairs(languages) do
  local ok, loaded = pcall(vim.treesitter.language.add, lang)
  if not ok or not loaded then
    vim.api.nvim_err_writeln("Missing parser: " .. lang)
    vim.cmd("cquit 1")
  end
end
vim.cmd("UpdateRemotePlugins")
vim.cmd("qa!")

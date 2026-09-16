-- No keybindings: those come from the learner's configuration snapshot.
return {
  -- Molten exports outputs on BufWritePost, so conversion must finish first.
  { "goerz/jupytext.nvim", opts = { async_write = false } },
  { "neovim/nvim-lspconfig", opts = function(_, opts)
    -- This workflow supplies Python tooling, not every workstation language server.
    for name, server in pairs(opts.servers) do
      if name ~= "*" then
        opts.servers[name] = vim.tbl_deep_extend("force", type(server) == "table" and server or {},
          { mason = false, enabled = name == "pyright" or name == "ruff" })
      end
    end
    opts.servers.pyright.settings = vim.tbl_deep_extend("force", opts.servers.pyright.settings or {},
      { python = { pythonPath = "/usr/local/bin/python" } })
  end },
  { "mason-org/mason.nvim", opts = function(_, opts) opts.ensure_installed = {} end },
  { "saghen/blink.cmp", opts = { fuzzy = { implementation = "lua" } } },
}

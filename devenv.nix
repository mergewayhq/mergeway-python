{ pkgs, lib, config, inputs, ... }:
let
  system = pkgs.stdenv.hostPlatform.system;
  mergeway-cli = inputs.mergeway-cli.packages.${system}.default;
in
{
  env.PYTHONPYCACHEPREFIX="${config.devenv.root}/.cache/cpython";

  packages = [
    pkgs.git
    mergeway-cli
  ];

  languages.python = {
    enable = true;
    uv = {
      enable = true;
      #sync.enable = true;
    };
  };

  git-hooks = {
    enable = true;
    package = pkgs.prek;
    
    hooks.ruff-format = {
      enable = true;
      pass_filenames = false;
    };

    hooks.unit-tests = {
      enable = true;
      name = "unit-tests";
      description = "Run Python unit tests";
      entry = "uv run python -m unittest";
      pass_filenames = false;
    };
  };
}

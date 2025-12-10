{
  description = "concurrency-bench";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";

    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.uv2nix.follows = "uv2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    fray = {
      url = "github:cmu-pasta/fray/fixnix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    {
      nixpkgs,
      pyproject-nix,
      uv2nix,
      pyproject-build-systems,
      fray,
      ...
    }:
    let
      inherit (nixpkgs) lib;
      forAllSystems = lib.genAttrs lib.systems.flakeExposed;

      workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };

      overlay = workspace.mkPyprojectOverlay {
        sourcePreference = "wheel";
      };

      editableOverlay = workspace.mkEditablePyprojectOverlay {
        root = "$REPO_ROOT";
      };

      pyprojectOverrides = final: prev: {
        func-timeout = prev."func-timeout".overrideAttrs (old: {
          buildInputs = (old.buildInputs or [ ]) ++ final.resolveBuildSystem { setuptools = [ ]; };
        });
      };

      pythonSets = forAllSystems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          python = pkgs.python3;
        in
        (pkgs.callPackage pyproject-nix.build.packages {
          inherit python;
        }).overrideScope
          (
            lib.composeManyExtensions [
              pyproject-build-systems.overlays.default
              overlay
              pyprojectOverrides
            ]
          )
      );

    in
    {
      devShells = forAllSystems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          pythonSet = pythonSets.${system}.overrideScope editableOverlay;
          virtualenv = pythonSet.mkVirtualEnv "dev-env" workspace.deps.all;
        in
        {
          default = pkgs.mkShell {
            packages = [
              virtualenv
              pkgs.uv
              pkgs.javaPackages.compiler.openjdk25
            ];
            env = {
              UV_NO_SYNC = "1";
              UV_PYTHON = pythonSet.python.interpreter;
              UV_PYTHON_DOWNLOADS = "never";
            };
            shellHook = ''
              unset PYTHONPATH
              export REPO_ROOT=$(git rev-parse --show-toplevel)
            '';
          };
        }
      );

      packages = forAllSystems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          pythonSet = pythonSets.${system}.overrideScope editableOverlay;
          virtualenv = pythonSet.mkVirtualEnv "dev-env" workspace.deps.all;

          repoSource = pkgs.runCommand "concurrency-bench-src" { } ''
            mkdir -p $out/workspace
            cp -r ${./.}/* $out/workspace/
          '';
        in
        {
          default = pythonSets.${system}.mkVirtualEnv "env" workspace.deps.default;

          dockerImage = pkgs.dockerTools.buildImage {
            name = "concurrency-bench";
            tag = "latest";

            copyToRoot = pkgs.buildEnv {
              name = "image-root";
              paths = [
                virtualenv
                pkgs.javaPackages.compiler.openjdk25
                pkgs.coreutils
                pkgs.bash
                pkgs.tmux
                pkgs.findutils
                pkgs.gnugrep
                pkgs.gnused
                pkgs.gawk
                pkgs.which
                pkgs.git
                repoSource
                fray.packages.${system}.default
              ];
              pathsToLink = [
                "/bin"
                "/workspace"
              ];
            };

            config = {
              Cmd = [ "${pkgs.bash}/bin/bash" ];
              WorkingDir = "/workspace";
              Env = [
                "PATH=/bin"
                "JAVA_HOME=${pkgs.javaPackages.compiler.openjdk25}"
                "REPO_ROOT=/workspace"
              ];
            };
          };
        }
      );
    };
}

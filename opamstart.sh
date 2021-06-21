opam init --auto-setup --dot-profile=~/.bash_profile
opam install taglib mad lame vorbis opus cry samplerate liquidsoap --confirm-level=unsafe-yes
eval $(opam env)
opam init --auto-setup --dot-profile=~/.bash_profile
opam install -y depext
opam depext taglib mad lame vorbis opus cry samplerate liquidsoap -y
opam install -y taglib mad lame vorbis opus cry samplerate liquidsoap
eval $(opam env)
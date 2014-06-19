GCC = g++
RM = rm -rf

.PHONY: all clean dll

ifeq (run,$(firstword $(MAKECMDGOALS)))
  # use the rest as arguments for "run"
  RUN_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  # ...and turn them into do-nothing targets
  $(eval $(RUN_ARGS):;@:)
endif


all: ANN

dll:
	g++ -shared -fPIC -o NNF.dll pm_minimal.cpp -DEXPORT_DLL -O6 -s -ffast-math -fomit-frame-pointer -fstrength-reduce -funroll-loops
	g++ -shared -fPIC -o NNF_center.dll pm_minimal_center.cpp -DEXPORT_DLL -O6 -s -ffast-math -fomit-frame-pointer -fstrength-reduce -funroll-loops


ANN: pm_minimal.cpp
	$(GCC) $< -o ANN

prog: 
	#..

run: ANN prog
	./ANN $(RUN_ARGS)


clean:
	$(RM) ANN ANN.exe
	$(RM) .raw .txt ann.raw annd.raw

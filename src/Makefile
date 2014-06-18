GCC = g++
RM = rm -rf

.PHONY: all clean

ifeq (run,$(firstword $(MAKECMDGOALS)))
  # use the rest as arguments for "run"
  RUN_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  # ...and turn them into do-nothing targets
  $(eval $(RUN_ARGS):;@:)
endif


all: ANN

%: %.o
	$(GCC) $< -o $@

%.o: pm_minimal.cpp
	$(GCC) $< -c
	mv pm_minimal.o ANN.o

prog: 
	#..

run: ./ANN prog
	./ANN $(RUN_ARGS)

dllmake: NNF.dll

dll: pm_minimal.cpp
	g++ -shared -fPIC -o NNF.dll pm_minimal.cpp -DEXPORT_DLL -g -O3

clean:
	$(RM) ANN ANN.exe
	$(RM) .raw .txt ann.raw annd.raw
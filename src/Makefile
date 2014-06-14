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

%: pm_minimal.cpp
	$(GCC) -DINT_MAX=100000 $< -o $@

prog: 
	#..

run: ./ANN prog
	./ANN $(RUN_ARGS)

clean:
	$(RM) ANN ANN.exe
	$(RM) .raw .txt ann.raw annd.raw
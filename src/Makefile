GCC = g++
RM = rm -rf

.PHONY: all clean

all: ANN

%: pm_minimal.cpp
	$(GCC) -DINT_MAX=100000 $< -o $@

run: ./ANN
	./ANN $(ARGS)

clean:
	$(RM) ANN
all: build/rop.bin

build/rop.bin: rop.py macros.py
	@python3 $(PYROP)/pyrop.py rop.py build/rop.bin

clean:
	@rm -rf build

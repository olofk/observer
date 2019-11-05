TOOLCHAIN_PREFIX ?= riscv64-unknown-elf-

g_sen.hex:
%.hex: %.bin
	python3 makehex.py $< 256 > $@
%.bin: %.elf
	$(TOOLCHAIN_PREFIX)objcopy -O binary $< $@

g_sen.elf: start.S g_sen.c
	$(TOOLCHAIN_PREFIX)gcc -Os -march=rv32i -mabi=ilp32 -nostdlib -o $@ \
		-Wl,-Bstatic,-Tlink.ld $^

clean:
	$(RM) *.elf *.hex

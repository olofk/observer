TOOLCHAIN_PREFIX ?= riscv64-unknown-elf-

user_btn.hex:

%.elf: %.S
	$(TOOLCHAIN_PREFIX)gcc -nostartfiles -march=rv32i -mabi=ilp32 -Tlink.ld -o$@ $<
%.hex: %.bin
	python3 makehex.py $< 256 > $@
%.bin: %.elf
	$(TOOLCHAIN_PREFIX)objcopy -O binary $< $@
clean:
	rm -f *.elf *.bin *.hex

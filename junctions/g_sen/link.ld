OUTPUT_ARCH( "riscv" )
/*ENTRY(_start)*/

MEMORY
{
    RAM (xrw)       : ORIGIN = 0x00000000, LENGTH = 0x04000 /* 1 KB */
}

SECTIONS
{
  .text : { *(.text) }
  .data : { *(.data) }
  .bss : { *(.bss) } >RAM
}

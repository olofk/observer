/*
* Read a string and send as packet to emitter
*
*
*/
#define AXIS_ADDR 0xC0000000
#define HALT_ADDR 0x90000000

	/*
	a0 = String address
	a1 = Emitter FIFO address
	t0 = Character to write
	*/

.globl _start
_start:
	nop
	/* Load string address to a0 */
	la	a0, str

	/* Load axis address to a1 */
	li	a1, AXIS_ADDR

	/* Write MSGPack string header (0b101xxxxx + len) */
	li	t0, 0xa0+20

next:	/* Write to FIFO */
	sb	t0, 0(a1)

	/* Read byte from str */
	lb	t0, 0(a0)

	/* Load next address */
	addi	a0, a0, 1

	/* Check if this was last byte in packet */
	bnez	t0, next

	/* Write packet end to FIFO */
	ori	t0, t0, 0x100
	sh	t0, 0(a1)

	li	t0, 10000
loop:	addi	t0, t0, -1
	bnez	t0, loop
	j _start

str:
	.string "SERV+FuseSoC rocks\n"

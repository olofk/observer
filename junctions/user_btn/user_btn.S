/*
* Track changes in user_btn
*
*/
#define COLL_ADDR 0x40000000
#define AXIS_ADDR 0xC0000000

	/*
	a0 = Collector address
	a1 = Emitter address
	*/

.globl _start
_start:
	/* Load collector address to a0 */
	li	a0, COLL_ADDR

	/* Load axis address to a1 */
	li	a1, AXIS_ADDR

	/* Clear t1 */
	addi	t1, zero, 0

	/* Read byte from collector */
next:	lb	t0, 0(a0)

	/* Check for changes */
	beq	t0, t1, next

	addi	t2, t0, 0x1c2
	/* Write to FIFO */
	sb	t2, 0(a1)

	mv	t1, t0
	j	next

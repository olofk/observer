#include <stdint.h>

#define COLL_ADDR 0x40000000
#define AXIS_ADDR 0xC0000000

#define SPI_OC_SIMPLE_SPCR (COLL_ADDR+4*0)
#define SPI_OC_SIMPLE_SPSR (COLL_ADDR+4*1)
#define SPI_OC_SIMPLE_SPDR (COLL_ADDR+4*2)
#define SPI_OC_SIMPLE_SPSS (COLL_ADDR+4*4)

#define ALWAYS_INLINE inline __attribute__((always_inline))

static ALWAYS_INLINE uint8_t sys_read8(uint32_t addr) {
  return *(volatile uint8_t *)addr;
}

static ALWAYS_INLINE void sys_write8(uint8_t data, uint32_t addr)
{
	*(volatile uint8_t *)addr = data;
}

static ALWAYS_INLINE void sys_write16(uint16_t data, uint32_t addr)
{
	*(volatile uint16_t *)addr = data;
}

void send_packet(uint8_t *addr, uint32_t len) {
  int i;
  for (i=0;i<len-1;i++)
    sys_write16(addr[i], AXIS_ADDR);

  sys_write16(0x100 | addr[i], AXIS_ADDR);
}
void spi_init(void) {
  uint8_t spcr = 0;
  spcr |= 0x11; /* clk/32 */

  /* Configure and Enable SPI controller */
  sys_write8(spcr | 0x40, SPI_OC_SIMPLE_SPCR);
}

void spi_xfer(uint8_t *wbuf, uint8_t *rbuf, int len) {
  int i;
  sys_write8(1, SPI_OC_SIMPLE_SPSS);
  for (i=0 ; i<len ; i++) {
    /* Write byte */
    sys_write8(wbuf[i], SPI_OC_SIMPLE_SPDR);

    /* Wait for rx FIFO empty flag to clear */
    while (sys_read8(SPI_OC_SIMPLE_SPSR) & 0x1) {
    }

    /* Get received byte */
    if (rbuf)
      rbuf[i] = sys_read8(SPI_OC_SIMPLE_SPDR);

  }

  sys_write8(0, SPI_OC_SIMPLE_SPSS);
}

void init_g_sen()
{
  unsigned char wbuf[3];

  wbuf[0]= 0x40 | 0x20;		// write multiple bytes with start address 0x20
  wbuf[1]= 0x37;		// 25Hz mode, low power off, enable axis Z Y X
  wbuf[2]= 0x00;		// all filters disabled

  spi_xfer(wbuf, 0, 3);

  wbuf[0]= 0x40 | 0x22;		// write multiple bytes with start address 0x22
  wbuf[1]= 0x00;		// all interrupts disabled
  wbuf[2]= 0x00;		// continous update, little endian, 2g full scale, high resolution disabled, self test disabled, 4 wire SPI

  spi_xfer(wbuf, 0, 3);
}

void main(void) {
  uint8_t msg[] = {0x80 | 1, //Fixmap with one element
		   0xa0 | 5, //String with 5 elements
		   'y','-','v','a','l',
		   0xd0, 0x00}; //Int 8 with placeholder value
  int msg_len = 9;

  uint8_t wbuf[3] = {0xC0 | 0x28, 0x0, 0x0}; // read y-register and increment
  uint8_t rbuf[3];
  int8_t values[4];
  int idx;
  uint16_t c;
  int8_t mean_val;
  volatile int dly;
  spi_init();
  init_g_sen();

  while (1) {

    spi_xfer(wbuf, rbuf, 3);
    values[(idx++)%4] = (int8_t)rbuf[1];
    mean_val = (values[0] + values[1] + values[2] + values[3])>>2;
    msg[8] = mean_val;
    send_packet(msg, msg_len);
    for (dly = 0;dly<10000;dly++);
  }
}

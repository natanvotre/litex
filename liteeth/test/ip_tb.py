from migen.fhdl.std import *
from migen.bus import wishbone
from migen.bus.transactions import *
from migen.sim.generic import run_simulation

from liteeth.common import *
from liteeth import LiteEthIPStack

from liteeth.test.common import *
from liteeth.test.model import phy, mac, arp, ip

ip_address = 0x12345678
mac_address = 0x12345678abcd

class TB(Module):
	def __init__(self):
		self.submodules.phy_model = phy.PHY(8, debug=False)
		self.submodules.mac_model = mac.MAC(self.phy_model, debug=False, loopback=False)
		self.submodules.arp_model = arp.ARP(self.mac_model, mac_address, ip_address, debug=False)
		self.submodules.ip_model = ip.IP(self.mac_model, mac_address, ip_address, debug=False, loopback=True)

		self.submodules.ip = LiteEthIPStack(self.phy_model, mac_address, ip_address)

		# use sys_clk for each clock_domain
		self.clock_domains.cd_eth_rx = ClockDomain()
		self.clock_domains.cd_eth_tx = ClockDomain()
		self.comb += [
			self.cd_eth_rx.clk.eq(ClockSignal()),
			self.cd_eth_rx.rst.eq(ResetSignal()),
			self.cd_eth_tx.clk.eq(ClockSignal()),
			self.cd_eth_tx.rst.eq(ResetSignal()),
		]

	def gen_simulation(self, selfp):
		selfp.cd_eth_rx.rst = 1
		selfp.cd_eth_tx.rst = 1
		yield
		selfp.cd_eth_rx.rst = 0
		selfp.cd_eth_tx.rst = 0

		for i in range(100):
			yield

		while True:
			selfp.ip.sink.stb = 1
			selfp.ip.sink.sop = 1
			selfp.ip.sink.eop = 1
			selfp.ip.sink.destination_ip_address = 0x12345678
			selfp.ip.sink.protocol = 0x11

			selfp.ip.source.ack = 1
			if selfp.ip.source.stb == 1 and selfp.ip.source.sop == 1:
				print("IP Packet / destination_ip_address %08x" %selfp.ip.sink.destination_ip_address)

			yield

if __name__ == "__main__":
	run_simulation(TB(), ncycles=2048, vcd_name="my.vcd", keep_files=True)

import unittest
from htmh_l2vpn.access_switch.access_switch import AccessSw


class TestAccessSw(unittest.TestCase):

    def setUp(self):
        self.sw = AccessSw(id='of:0000068f79daf149', public_mac='00:29:15:80:4E:4A')

        self.test_ips = ['10.0.0.10', '10.0.0.11', '10.0.0.30']
        self.test_mapped_ips = ['10.0.1.10', '10.0.1.11', '10.0.1.30']

        self.test_macs = ['01:00:00:00:00:FF', '02:00:00:00:FF:FF', '03:00:00:FF:FF:FF']

        self.test_ports = [4, 5, 6]

        # Define hosts to test
        for i in range(len(self.test_macs)):
            self.sw.add_host(ip=self.test_ips[i], mac=self.test_macs[i], port=self.test_ports[i])

        self.test_foreign_host = {'00:29:15:80:AA:FF': {'mapped_ip': '10.0.0.12', 'port': 10}}
        self.sw.add_foreign_hosts(src_device_mac='00:29:15:DD:FF:ff', hosts=self.test_foreign_host)

    def tearDown(self):
        pass

    def test_instancing(self):
        """Test assert warnings when ID and/or Mac with no legit format is
         passed at the moment of Instancing."""
        with self.assertWarns(ImportWarning):
            AccessSw('dsfasdfasf', '00:29:15:80:4E:4A')
            AccessSw('of:gfgafgfdgfgdfg', '00:29:15:80:4E:4A')
            AccessSw('of:0000c27e34dffd4f', 'dafdsfasdf')


        """Test if an object is an instance successful in spite of upper
         or lower string values."""
        self.assertIsInstance(AccessSw('of:0000c27e34dffd4f'.upper(), '00:29:15:80:4E:4A'), AccessSw)
        self.assertIsInstance(AccessSw('of:0000c27e34dffd4f', '00:29:15:80:4E:4A'.lower()), AccessSw)

    def test_add_host(self):
        hosts = {1: {'ip': '10.0.0.256', 'mac': '00:29:15:80:AA:AA', 'port': 4},
                 2: {'ip': '10.0.0.2', 'mac': '00:29:15:80:AA', 'port': 5}}

        """Test the function can identify invalid IP ranges and non-legit MAC formats"""
        with self.assertLogs():
            self.sw.add_host(ip=hosts[1]['ip'], mac=hosts[1]['mac'], port=hosts[1]['port'])
            self.sw.add_host(ip=hosts[2]['ip'], mac=hosts[2]['mac'], port=hosts[2]['port'])

        """"Test if a host is not added after invalid values"""
        self.assertNotIn(hosts[1]['mac'].lower(), self.sw.hosts.keys())
        self.assertNotIn(hosts[2]['mac'].lower(), self.sw.hosts.keys())

        """Test if a host can be added successfully."""
        self.assertIn(self.test_macs[1].lower(), self.sw.hosts.keys())

    def test_add_foreign_hosts(self):
        host = {'00:29:15:80:AA:AA': {'mapped_ip': '10.0.0.2', 'port': 5}}

        """Test the function can identify non-legit MAC formats"""
        with self.assertLogs():
            self.sw.add_foreign_hosts('00:29:15:GG:RR:RR', host)
            self.sw.add_foreign_hosts('1234', host)

        """"Test if a host is not added after invalid values"""
        self.assertNotIn('00:29:15:GG:RR:RR', self.sw.foreign_hosts.keys())
        self.assertNotIn('1234', self.sw.foreign_hosts.keys())

        """Test if foreign hosts are added successfully."""
        self.assertIn('00:29:15:80:AA:FF'.lower(), self.sw.foreign_hosts.keys())

    def test_map_ips(self):
        self.assertEqual(self.sw.map_ips(1), self.test_mapped_ips)

    def test_wipe_hosts(self):
        self.sw.wipe_hosts()
        self.assertDictEqual(self.sw.hosts, {})

    def test_wipe_foreign_hosts(self):
        self.sw.wipe_foreign_hosts()
        self.assertDictEqual(self.sw.foreign_hosts, {})

    def test_port_list(self):
        pass

    def test_all_hosts(self):
        pass

    def test_pairs_macs(self):
        pass




if __name__ == '__main__':
    unittest.main()

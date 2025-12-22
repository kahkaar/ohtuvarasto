import unittest

from varasto import Varasto


class TestVarasto(unittest.TestCase):
    def setUp(self):
        self.varasto = Varasto(10)

    def test_konstruktori_luo_tyhjan_varaston(self):
        # https://docs.python.org/3/library/unittest.html#unittest.TestCase.assertAlmostEqual
        self.assertAlmostEqual(self.varasto.saldo, 0)

    def test_uudella_varastolla_oikea_tilavuus(self):
        self.assertAlmostEqual(self.varasto.tilavuus, 10)

    def test_lisays_lisaa_saldoa(self):
        self.varasto.lisaa_varastoon(8)

        self.assertAlmostEqual(self.varasto.saldo, 8)

    def test_lisays_lisaa_pienentaa_vapaata_tilaa(self):
        self.varasto.lisaa_varastoon(8)

        # vapaata tilaa pitäisi vielä olla tilavuus-lisättävä määrä eli 2
        self.assertAlmostEqual(self.varasto.paljonko_mahtuu(), 2)

    def test_ottaminen_palauttaa_oikean_maaran(self):
        self.varasto.lisaa_varastoon(8)

        saatu_maara = self.varasto.ota_varastosta(2)

        self.assertAlmostEqual(saatu_maara, 2)

    def test_ottaminen_lisaa_tilaa(self):
        self.varasto.lisaa_varastoon(8)

        self.varasto.ota_varastosta(2)

        # varastossa pitäisi olla tilaa 10 - 8 + 2 eli 4
        self.assertAlmostEqual(self.varasto.paljonko_mahtuu(), 4)

    def test_lisaa_liikaa(self):
        self.varasto.lisaa_varastoon(12)

        self.assertAlmostEqual(self.varasto.saldo, 10)

    def test_ota_liikaa(self):
        self.varasto.lisaa_varastoon(8)

        saatu_maara = self.varasto.ota_varastosta(12)

        self.assertAlmostEqual(saatu_maara, 8)

    def test_alusta_tilavuus_negatiivisella(self):
        varasto = Varasto(-10)

        self.assertAlmostEqual(varasto.tilavuus, 0)

    def test_alusta_saldo_negatiivisella(self):
        varasto = Varasto(10, -8)

        self.assertAlmostEqual(varasto.saldo, 0)

    def test_alusta_tilavuus_saldo_negatiivisella(self):
        varasto = Varasto(-10, -8)

        self.assertAlmostEqual(varasto.tilavuus, 0)
        self.assertAlmostEqual(varasto.saldo, 0)

    def test_lisaa_negatiivinen(self):
        self.varasto.lisaa_varastoon(-8)

        self.assertAlmostEqual(self.varasto.saldo, 0)

    def test_ota_negatiivinen(self):
        saatu_maara = self.varasto.ota_varastosta(-8)

        self.assertAlmostEqual(saatu_maara, 0)

    def test_str_palautus(self):
        saldo = 3.0
        self.varasto.lisaa_varastoon(saldo)

        tulos = f"saldo = {saldo}, vielä tilaa 7.0"
        self.assertEqual(str(self.varasto), tulos)

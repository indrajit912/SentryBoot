import unittest
from sentryboot.config.manager import hash_passphrase, verify_passphrase, encrypt_secret, decrypt_secret

class TestAuthAndConfig(unittest.TestCase):
    
    def test_passphrase_hashing_and_verification(self):
        passphrase = "my-super-secret-passphrase"
        
        # Hash the passphrase
        h_hex, s_hex = hash_passphrase(passphrase)
        
        self.assertIsNotNone(h_hex)
        self.assertIsNotNone(s_hex)
        self.assertEqual(len(h_hex), 64)  # SHA-256 is 32 bytes (64 hex characters)
        self.assertEqual(len(s_hex), 32)  # Salt is 16 bytes (32 hex characters)
        
        # Verify correct passphrase
        self.assertTrue(verify_passphrase(passphrase, h_hex, s_hex))
        
        # Verify incorrect passphrase
        self.assertFalse(verify_passphrase("wrong-passphrase", h_hex, s_hex))
        self.assertFalse(verify_passphrase("", h_hex, s_hex))
        
    def test_passphrase_salting_uniqueness(self):
        passphrase = "test-passphrase"
        
        h1, s1 = hash_passphrase(passphrase)
        h2, s2 = hash_passphrase(passphrase)
        
        # Salts should be random and unique
        self.assertNotEqual(s1, s2)
        self.assertNotEqual(h1, h2)
        
    def test_secret_encryption_decryption(self):
        secret = "HermesAPIKey12345"
        
        encrypted = encrypt_secret(secret)
        self.assertTrue(encrypted.startswith(("dpapi:", "plain:")))
        
        decrypted = decrypt_secret(encrypted)
        self.assertEqual(secret, decrypted)
        
    def test_email_formatting(self):
        from sentryboot.notifications.formatter import format_alert_email, format_test_email
        diagnostics = {
            "computer_name": "TEST-PC",
            "username": "testuser",
            "local_ip": "127.0.0.1",
            "public_ip": "8.8.8.8",
            "uptime_str": "0:01:00",
            "boot_time_str": "Jul 09, 26 06:42:13 PM"
        }
        
        alert_html = format_alert_email("Test Event", diagnostics)
        self.assertIsInstance(alert_html, str)
        self.assertIn("Test Event", alert_html)
        self.assertIn("TEST-PC", alert_html)
        
        test_html = format_test_email(diagnostics)
        self.assertIsInstance(test_html, str)
        self.assertIn("TEST-PC", test_html)

if __name__ == '__main__':
    unittest.main()

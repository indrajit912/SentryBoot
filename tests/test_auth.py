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
        
    def test_config_timeout_parameter(self):
        from sentryboot.config.manager import ConfigManager
        import tempfile
        from pathlib import Path
        
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "config.json"
            
            old_file = ConfigManager.CONFIG_FILE
            try:
                ConfigManager.CONFIG_FILE = test_file
                config = ConfigManager()
                
                self.assertEqual(config.default_timeout_mins, 2)
                
                config.set_credentials(
                    api_key="api_key_test",
                    bot_id="bot_id_test",
                    recipient="test@example.com",
                    passphrase="pass",
                    default_timeout_mins=5
                )
                self.assertEqual(config.default_timeout_mins, 5)
                config.save()
                
                config2 = ConfigManager()
                config2.load()
                self.assertEqual(config2.default_timeout_mins, 5)
                self.assertEqual(config2.recipient_email, "test@example.com")
            finally:
                ConfigManager.CONFIG_FILE = old_file
        
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

    def test_webcam_graceful_on_no_webcam(self):
        # Even if webcam doesn't exist, capture_snapshot should not raise exception but return None or Path
        from sentryboot.utils.camera import capture_snapshot
        import tempfile
        from pathlib import Path
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = capture_snapshot(Path(tmpdir))
            self.assertTrue(path is None or isinstance(path, Path))

    def test_webcam_missing_mock(self):
        from unittest.mock import patch, MagicMock
        from sentryboot.utils.camera import capture_snapshot
        from pathlib import Path
        
        with patch('cv2.VideoCapture') as mock_video:
            mock_cap = MagicMock()
            mock_cap.isOpened.return_value = False
            mock_video.return_value = mock_cap
            
            res = capture_snapshot(Path("."))
            self.assertIsNone(res)

    def test_webcam_success_mock(self):
        from unittest.mock import patch, MagicMock
        import numpy as np
        from sentryboot.utils.camera import capture_snapshot
        from pathlib import Path
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            with patch('cv2.VideoCapture') as mock_video, patch('cv2.imwrite') as mock_imwrite:
                mock_cap = MagicMock()
                mock_cap.isOpened.return_value = True
                
                # Mock cap.read() returning True and a dummy image frame (numpy array)
                dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                mock_cap.read.return_value = (True, dummy_frame)
                mock_video.return_value = mock_cap
                
                # Mock imwrite to actually write a dummy file (to simulate success)
                def fake_imwrite(filename, img, params=None):
                    with open(filename, 'wb') as f:
                        f.write(b"fake image data")
                    return True
                mock_imwrite.side_effect = fake_imwrite
                
                res = capture_snapshot(tmp_path)
                self.assertIsNotNone(res)
                self.assertTrue(res.exists())
                self.assertIn("intruder_", res.name)

    def test_webcam_permission_denied_mock(self):
        from unittest.mock import patch, MagicMock
        from sentryboot.utils.camera import capture_snapshot
        from pathlib import Path
        
        with patch('cv2.VideoCapture') as mock_video:
            mock_cap = MagicMock()
            mock_cap.isOpened.return_value = True
            mock_cap.read.side_effect = Exception("Permission Denied")
            mock_video.return_value = mock_cap
            
            res = capture_snapshot(Path("."))
            self.assertIsNone(res)

    def test_reset_state_successful_cleanup(self):
        from sentryboot.config.manager import ConfigManager
        import tempfile
        from pathlib import Path
        
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / ".sentryboot"
            test_dir.mkdir()
            
            # Create mock config, logs, and snapshots
            config_file = test_dir / "config.json"
            config_file.write_text('{"mock": true}')
            
            log_file = test_dir / "boot.log"
            log_file.write_text("mock log")
            log_file_rot = test_dir / "boot.log.1"
            log_file_rot.write_text("mock log rot")
            
            snapshots_dir = test_dir / "snapshots"
            snapshots_dir.mkdir()
            snap_file = snapshots_dir / "intruder_mock.jpg"
            snap_file.write_text("mock image")
            
            # Temporarily patch CONFIG_DIR and CONFIG_FILE in ConfigManager
            old_dir = ConfigManager.CONFIG_DIR
            old_file = ConfigManager.CONFIG_FILE
            
            try:
                ConfigManager.CONFIG_DIR = test_dir
                ConfigManager.CONFIG_FILE = config_file
                
                # Check they exist
                self.assertTrue(config_file.exists())
                self.assertTrue(log_file.exists())
                self.assertTrue(log_file_rot.exists())
                self.assertTrue(snap_file.exists())
                self.assertTrue(snapshots_dir.exists())
                
                # Call reset_state()
                summary = ConfigManager.reset_state()
                
                # Verify they are deleted
                self.assertFalse(config_file.exists())
                self.assertFalse(log_file.exists())
                self.assertFalse(log_file_rot.exists())
                self.assertFalse(snap_file.exists())
                self.assertFalse(snapshots_dir.exists())
                self.assertTrue(test_dir.exists())  # Directory is recreated
                
                self.assertTrue(summary["config_deleted"])
                self.assertTrue(summary["logs_deleted"])
                self.assertEqual(summary["snapshots_deleted"], 1)
                
                # Run reset_state again to test idempotency (should run fine without errors)
                summary2 = ConfigManager.reset_state()
                self.assertFalse(summary2["config_deleted"])
                self.assertFalse(summary2["logs_deleted"])
                self.assertEqual(summary2["snapshots_deleted"], 0)
                
            finally:
                ConfigManager.CONFIG_DIR = old_dir
                ConfigManager.CONFIG_FILE = old_file

    def test_reset_state_when_no_data_exists(self):
        from sentryboot.config.manager import ConfigManager
        import tempfile
        from pathlib import Path
        
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "empty_dir"
            
            old_dir = ConfigManager.CONFIG_DIR
            old_file = ConfigManager.CONFIG_FILE
            try:
                ConfigManager.CONFIG_DIR = test_dir
                ConfigManager.CONFIG_FILE = test_dir / "config.json"
                
                self.assertFalse(test_dir.exists())
                
                # Call reset_state
                summary = ConfigManager.reset_state()
                
                # Verify directory was created and no errors raised
                self.assertTrue(test_dir.exists())
                self.assertFalse(summary["config_deleted"])
                self.assertFalse(summary["logs_deleted"])
                self.assertEqual(summary["snapshots_deleted"], 0)
            finally:
                ConfigManager.CONFIG_DIR = old_dir
                ConfigManager.CONFIG_FILE = old_file

    def test_dynamic_timing_display_in_panel(self):
        from sentryboot.authentication.auth import build_ui_panel
        from rich.console import Console
        
        console = Console(width=80)
        
        # Test exact minute conversion
        panel_2m = build_ui_panel(remaining=120, max_time=120, input_masked="", attempts_left=3, status_msg="")
        with console.capture() as capture:
            console.print(panel_2m)
        self.assertIn("2 minute(s)", capture.get())
        
        # Test non-exact minute (seconds) conversion
        panel_45s = build_ui_panel(remaining=45, max_time=45, input_masked="", attempts_left=3, status_msg="")
        with console.capture() as capture:
            console.print(panel_45s)
        self.assertIn("45 seconds", capture.get())

    def test_hermes_client_attachments_payload(self):
        from unittest.mock import patch, MagicMock
        from sentryboot.emailer.client import HermesClient
        
        client = HermesClient("https://mock-hermes", "mock-key", "mock-bot")
        attachments = [{"filename": "pic.jpg", "content": "base64data"}]
        
        with patch('requests.post') as mock_post:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"success": True}
            mock_post.return_value = mock_resp
            
            client.send_email(
                to_emails="test@example.com",
                subject="Test Subject",
                body_html="<h1>Test</h1>",
                attachments=attachments
            )
            
            mock_post.assert_called_once()
            kwargs = mock_post.call_args[1]
            payload = kwargs["json"]
            self.assertEqual(payload["attachments"], attachments)

    def test_send_alert_email_incorporates_snapshot_attachment(self):
        from unittest.mock import patch, MagicMock
        from sentryboot.authentication.auth import send_alert_email
        from sentryboot.config.manager import ConfigManager
        from pathlib import Path
        
        config = ConfigManager()
        config.hermes_base_url = "https://mock-hermes"
        config.hermes_api_key = "mock-key"
        config.hermes_emailbot_id = "mock-bot"
        config.recipient_email = "test@example.com"
        
        with patch('sentryboot.authentication.auth.capture_snapshot') as mock_capture, \
             patch('sentryboot.authentication.auth.open', create=True) as mock_open, \
             patch('sentryboot.authentication.auth.HermesClient') as mock_hermes_class:
            
            mock_path = MagicMock(spec=Path)
            mock_path.exists.return_value = True
            mock_path.name = "intruder_pic.jpg"
            mock_capture.return_value = mock_path
            
            mock_file = MagicMock()
            mock_file.read.return_value = b"raw image bytes"
            mock_open.return_value.__enter__.return_value = mock_file
            
            mock_client = MagicMock()
            mock_hermes_class.return_value = mock_client
            
            send_alert_email("Test Intrusion", config)
            
            mock_client.send_email.assert_called_once()
            called_kwargs = mock_client.send_email.call_args[1]
            self.assertIn("attachments", called_kwargs)
            self.assertIsNotNone(called_kwargs["attachments"])
            self.assertEqual(called_kwargs["attachments"][0]["filename"], "intruder_pic.jpg")
            self.assertEqual(called_kwargs["attachments"][0]["content"], "cmF3IGltYWdlIGJ5dGVz")

    def test_display_welcome_dashboard(self):
        from sentryboot.authentication.dashboard import display_welcome_dashboard
        from sentryboot.config.manager import ConfigManager
        from rich.console import Console
        
        config = ConfigManager()
        config.recipient_email = "test@example.com"
        
        console = Console(width=80)
        with console.capture() as capture:
            display_welcome_dashboard(config, console=console)
            
        output = capture.get()
        self.assertIn("SENTRYBOOT ACCESS GRANTED", output)
        self.assertIn("SYSTEM INFO", output)
        self.assertIn("SECURITY INFO", output)
        self.assertIn("Recipient Email", output)

    def test_forensics_gathering(self):
        from sentryboot.utils.forensics import gather_forensics, get_process_snapshot, get_network_snapshot
        
        procs = get_process_snapshot()
        self.assertIsInstance(procs, str)
        self.assertTrue(len(procs) > 0)
        
        net = get_network_snapshot()
        self.assertIsInstance(net, str)
        self.assertTrue(len(net) > 0)
        
        forensics = gather_forensics()
        self.assertIn("processes.txt", forensics)
        self.assertIn("network_connections.txt", forensics)
        self.assertTrue(len(forensics["processes.txt"]) > 0)
        self.assertTrue(len(forensics["network_connections.txt"]) > 0)

    def test_offline_alert_caching_and_sync(self):
        from sentryboot.utils.caching import cache_alert, sync_cached_alerts
        import sentryboot.utils.caching as caching
        from sentryboot.config.manager import ConfigManager
        import tempfile
        import json
        from pathlib import Path
        from unittest.mock import patch, MagicMock
        
        with tempfile.TemporaryDirectory() as tmpdir:
            test_cache_dir = Path(tmpdir) / "cache"
            
            # Patch CACHE_DIR
            old_cache_dir = caching.CACHE_DIR
            caching.CACHE_DIR = test_cache_dir
            
            try:
                # Cache an alert
                reason = "Mock Threat"
                diagnostics = {"computer_name": "TEST-PC"}
                forensics_data = {"processes.txt": "proc1", "network_connections.txt": "conn1"}
                
                cache_alert(reason, diagnostics, "snap.jpg", "b64img", forensics_data)
                
                # Check file created
                json_files = list(test_cache_dir.glob("*.json"))
                self.assertEqual(len(json_files), 1)
                
                # Verify content
                with open(json_files[0], "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.assertEqual(data["reason"], reason)
                self.assertEqual(data["diagnostics"], diagnostics)
                self.assertEqual(data["snapshot_name"], "snap.jpg")
                self.assertEqual(data["snapshot_base64"], "b64img")
                self.assertEqual(data["forensics"], forensics_data)
                
                # Sync cache with mocked HermesClient
                config = ConfigManager()
                config.hermes_base_url = "https://mock-hermes"
                config.hermes_api_key = "mock-key"
                config.hermes_emailbot_id = "mock-bot"
                config.recipient_email = "test@example.com"
                
                with patch('sentryboot.utils.caching.HermesClient') as mock_hermes_class:
                    mock_client = MagicMock()
                    mock_hermes_class.return_value = mock_client
                    
                    sync_cached_alerts(config)
                    
                    # Assert client.send_email was called once and cache cleared
                    mock_client.send_email.assert_called_once()
                    self.assertEqual(len(list(test_cache_dir.glob("*.json"))), 0)
            finally:
                caching.CACHE_DIR = old_cache_dir

    def test_lock_workstation_call(self):
        from unittest.mock import patch
        from sentryboot.authentication.auth import lock_workstation
        
        # Test Windows lock call mock
        with patch('sys.platform', 'win32'), \
             patch('ctypes.windll.user32.LockWorkStation') as mock_lock:
            lock_workstation()
            mock_lock.assert_called_once()
            
        # Test macOS screen saver call mock
        with patch('sys.platform', 'darwin'), \
             patch('os.system') as mock_sys:
            lock_workstation()
            mock_sys.assert_called_once_with('pmset displaysleepnow')
            
        # Test Linux screensaver lock mock
        with patch('sys.platform', 'linux'), \
             patch('os.system') as mock_sys:
            lock_workstation()
            mock_sys.assert_called_once_with('xdg-screensaver lock')

if __name__ == '__main__':
    unittest.main()

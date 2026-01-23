import sys
import os
import time
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer, QIODevice, QMimeData, QByteArray, QBuffer
from PyQt5.QtGui import QImage, QClipboard
import argparse
from filelock import FileLock, Timeout
import logging
import json
import base64



class ClipboardSync:
    def __init__(self):
        self.file_path = Path(args.file)
        self.lock_path = self.file_path.with_name(self.file_path.name + '.lock')

        self.app = QApplication(sys.argv)
        self.clipboard = QApplication.clipboard()
        self.local_version = 0
        self.last_file_version = 0
        self.last_file_mtime = 0
        self.last_clipboard_text = ''
        self.last_clipboard_image = ''
        self.lock = FileLock(self.lock_path, timeout=10)

        # Read file version
        if self.file_path.exists():
            file_content = self.read_from_file()
            if file_content:
                self.last_file_version = file_content.get('version', 0)
                logging.info(f'update last_file_version={self.last_file_version}')
                self.local_version = self.last_file_version

        # Timer to check clipboard and file changes
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_clipboard_and_file)
        self.timer.start(1000)  # Check every second

    def check_clipboard_and_file(self):
        self.check_clipboard()
        self.check_file()

    def check_clipboard(self):
        # logging.info('check_clipboard')
        mime_data = self.clipboard.mimeData()
        content_changed = False
        content_type = None
        content = None

        if mime_data.hasText():
            content_type = 'TEXT'
            content = self.clipboard.text()

            if mime_data.hasFormat('text/uri-list') and content.startswith('file:///'):
                logging.info(f'content={content}')
                return

            if self.last_clipboard_text != content:
                content_changed = True
            self.last_clipboard_text = content
        elif mime_data.hasImage():
            content_type = 'IMAGE'
            img = self.clipboard.image()
            byte_array = QByteArray()
            buffer = QBuffer(byte_array)
            buffer.open(QIODevice.WriteOnly)
            img.save(buffer, 'PNG')
            content = base64.b64encode(byte_array.data()).decode('ascii')
            if self.last_clipboard_image != content:
                content_changed = True
            self.last_clipboard_image = content
        else:
            return  # Unsupported content type

        if content_changed:
            self.local_version += 1
            content_to_save = {
                'version': self.local_version,
                'content_type': content_type,
                'data': content
            }
            self.write_to_file(content_to_save)
            self.last_file_version = self.local_version
            logging.info(f'write {content_type} from clipboard(v{self.local_version}) to file(v{self.last_file_version})')

    def write_to_file(self, content_dict):
        # temp_file = self.file_path.with_suffix('.tmp')
        try:
            with self.lock:
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    json.dump(content_dict, f)
                # temp_file.replace(self.file_path)
                logging.info(f'Content written to file: {self.file_path}, size={len(content_dict["data"])}')
        except Exception as e:
            logging.exception('Error writing to file: %s', e)
        # finally:
            # if temp_file.exists():
                # try:
                    # temp_file.unlink()
                # except Exception as e:
                    # logging.warning('Failed to remove temporary file: %s', e)

    def check_file(self):
        if not self.file_path.exists():
            logging.debug('File does not exist: %s', self.file_path)
            return  # File not exists, do nothing

        try:
            current_mtime = os.path.getmtime(self.file_path)
        except OSError as e:
            logging.error('Error getting file mtime: %s', e)
            return

        if current_mtime != self.last_file_mtime:
            logging.info(f'file changed, diff={current_mtime - self.last_file_mtime:.2f}s')
            self.last_file_mtime = current_mtime
            file_content = self.read_from_file()
            if file_content:
                file_version = file_content.get('version', 0)
                logging.info(f'read file, file_ver={file_version}, local_ver={self.local_version}')
                if file_version > self.local_version:
                    self.update_clipboard(file_content)
                    self.last_file_version = file_version
                    self.local_version = file_version
                    logging.info(f'write file(v{self.last_file_version}) to clipboard(v{self.local_version})')

    def read_from_file(self):
        try:
            with self.lock:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                logging.debug(f'Content read from file: {self.file_path}, size={len(content["data"])}')
                return content
        except Exception as e:
            logging.error('Error reading file: %s', e)
            return None

    def update_clipboard(self, content_dict):
        content_type = content_dict.get('content_type')
        data = content_dict.get('data', '')

        if content_type == 'TEXT':
            try:
                self.clipboard.setText(data)
                self.last_clipboard_text = data
                logging.info(f'{content_type} set to clipboard, size={len(data)}')
            except Exception as e:
                logging.exception(f'Set {content_type} to clipboard failed: {e}')

        elif content_type == 'IMAGE':
            try:
                byte_data = base64.b64decode(data)

                # 创建 QImage 并验证数据
                image = QImage()
                if image.loadFromData(byte_data):
                    mime_data = QMimeData()
                    ba = QByteArray(byte_data)

                    # 设置多种 MIME 类型以提高兼容性
                    mime_data.setData('image/png', ba)
                    mime_data.setData('image/jpeg', ba)
                    mime_data.setData('image/bmp', ba)

                    # 设置标准图像数据
                    mime_data.setImageData(QImage.fromData(byte_data))

                    # 清除剪贴板并设置新数据
                    self.clipboard.clear()
                    self.clipboard.setMimeData(mime_data)

                    self.last_clipboard_image = data
                    logging.info(f'{content_type} set to clipboard, size={len(data)}')

                    # 验证剪贴板内容
                    if self.clipboard.mimeData().hasImage():
                        logging.info('Clipboard confirmed to contain image data')
                    else:
                        logging.warning('Clipboard does not contain recognized image data')
                else:
                    logging.warning('Invalid image data. Failed to load image from decoded data.')

            except Exception as e:
                logging.exception(f'Set {content_type} to clipboard failed: {e}')

        else:
            logging.warning(f'Unexpected content type {content_type}, size={len(data)}')

    def run(self):
        sys.exit(self.app.exec_())

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(message)s',
                        handlers=[
                            logging.StreamHandler(),  # Console handler
                            logging.FileHandler('clipman.log', mode='w')  # File handler
                        ])

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Clipboard sync between two machines.')
    parser.add_argument('-f', '--file', default='sync.json')
    args = parser.parse_args()

    sync = ClipboardSync()
    sync.run()
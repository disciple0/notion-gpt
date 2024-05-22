from pathlib import Path

file_path = 'components/guides/try_now_guide.md'
markdown_content = Path(file_path).read_text()
print(markdown_content)
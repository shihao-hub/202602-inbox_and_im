#!/usr/bin/env python3
"""
JWT SECRET_KEY 动态生成工具

用于生成安全的随机密钥，并可选择性地更新到 .env 文件中。
"""
import secrets
import os
import sys
import re
from pathlib import Path
from typing import Optional


def generate_secret_key(length: int = 64) -> str:
    """
    生成安全的随机密钥

    Args:
        length: 密钥长度（默认64字符）

    Returns:
        生成的密钥字符串
    """
    # 使用 secrets.token_urlsafe 生成安全的随机密钥
    # base64 编码，每 3 字节生成 4 个字符
    # 为了确保至少 length 个字符，我们生成稍长一点
    byte_length = (length * 3) // 4 + 1
    secret = secrets.token_urlsafe(byte_length)

    # 截取到指定长度
    return secret[:length]


def update_env_file(env_path: Path, new_key: str, backup: bool = True) -> bool:
    """
    更新 .env 文件中的 SECRET_KEY

    Args:
        env_path: .env 文件路径
        new_key: 新的密钥
        backup: 是否创建备份文件

    Returns:
        是否成功更新
    """
    if not env_path.exists():
        print(f"错误: .env 文件不存在于 {env_path}")
        return False

    try:
        # 读取原文件内容
        with open(env_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 创建备份
        if backup:
            backup_path = env_path.with_suffix('.env.backup')
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"已创建备份文件: {backup_path}")

        # 替换 SECRET_KEY
        pattern = r'^SECRET_KEY=.*$'
        replacement = f'SECRET_KEY={new_key}'

        new_content = re.sub(
            pattern,
            replacement,
            content,
            flags=re.MULTILINE
        )

        # 如果没有找到 SECRET_KEY，在 JWT 配置部分添加
        if new_content == content:
            # 查找 JWT 配置部分
            jwt_section = re.search(
                r'# JWT 配置.*?\n',
                content,
                flags=re.DOTALL
            )
            if jwt_section:
                # 在 JWT 配置注释后添加
                insert_pos = jwt_section.end()
                new_content = (
                    content[:insert_pos] +
                    f'SECRET_KEY={new_key}\n' +
                    content[insert_pos:]
                )
            else:
                # 在文件末尾添加
                new_content = content + f'\n# JWT 配置\nSECRET_KEY={new_key}\n'

        # 写入新内容
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f"[成功] 已成功更新 {env_path} 中的 SECRET_KEY")
        return True

    except Exception as e:
        print(f"错误: 更新文件失败 - {e}")
        return False


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description='JWT SECRET_KEY 动态生成工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 生成密钥并显示
  python scripts/generate_secret_key.py

  # 生成密钥并更新到 .env 文件（交互式确认）
  python scripts/generate_secret_key.py --update

  # 生成密钥并直接更新 .env 文件（不确认）
  python scripts/generate_secret_key.py --update --yes

  # 生成指定长度的密钥
  python scripts/generate_secret_key.py --length 128

  # 指定 .env 文件路径
  python scripts/generate_secret_key.py --update --env-path .env.example
        '''
    )

    parser.add_argument(
        '-l', '--length',
        type=int,
        default=64,
        help='密钥长度（默认64字符）'
    )

    parser.add_argument(
        '-u', '--update',
        action='store_true',
        help='更新到 .env 文件'
    )

    parser.add_argument(
        '-y', '--yes',
        action='store_true',
        help='跳过确认直接更新'
    )

    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='不创建备份文件'
    )

    parser.add_argument(
        '--env-path',
        type=str,
        default='.env',
        help='.env 文件路径（默认: .env）'
    )

    args = parser.parse_args()

    # 生成密钥
    secret_key = generate_secret_key(args.length)

    print(f"\n生成的 SECRET_KEY (长度: {len(secret_key)}):")
    print("=" * 70)
    print(secret_key)
    print("=" * 70)

    # 如果不更新文件，直接返回
    if not args.update:
        print("\n提示: 使用 --update 参数可以将密钥更新到 .env 文件")
        return 0

    # 确认更新
    if not args.yes:
        response = input(f"\n确定要更新 {args.env_path} 文件吗？(y/N): ")
        if response.lower() not in ['y', 'yes']:
            print("已取消")
            return 0

    # 更新 .env 文件
    env_path = Path(args.env_path)

    # 如果是相对路径，从项目根目录开始
    if not env_path.is_absolute():
        # 获取项目根目录（scripts 目录的父目录）
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        env_path = project_root / env_path

    success = update_env_file(
        env_path,
        secret_key,
        backup=not args.no_backup
    )

    if success:
        print("\n[成功] 操作完成")
        print("\n重要提示:")
        print("  1. 请妥善保管生成的 SECRET_KEY")
        print("  2. 不要将 SECRET_KEY 提交到版本控制系统")
        print("  3. 生产环境应使用环境变量或密钥管理服务")
        return 0
    else:
        print("\n[失败] 操作失败")
        return 1


if __name__ == '__main__':
    sys.exit(main())

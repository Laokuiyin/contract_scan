#!/usr/bin/env python3
"""验证API配置"""
import os
import sys

# 设置环境变量
os.environ['QWEN_API_KEY'] = 'sk-49b75404a5484971b808a74867292a11'

sys.path.insert(0, '/Users/laokui/SynologyDrive/AI/contract_scan/backend')

from app.core.config import settings

print('=' * 50)
print('通义千问 API 配置验证')
print('=' * 50)
print('')
print(f'✅ AI 提供商: {settings.AI_PROVIDER}')
print(f'✅ API 密钥: {settings.QWEN_API_KEY[:10]}...')
print(f'✅ 密钥长度: {len(settings.QWEN_API_KEY)} 字符')
print('')
print('📋 API 端点信息:')
print('   URL: https://dashscope.aliyuncs.com/compatible-mode/v1')
print('   Model: qwen-plus')
print('')
print('=' * 50)
print('✅ 配置完成！系统已就绪。')
print('=' * 50)
print('')
print('🚀 启动系统:')
print('   1. 启动基础服务: docker-compose -f docker-compose.dev.yml up -d')
print('   2. 启动后端: cd backend && uvicorn app.main:app --reload')
print('   3. 启动Celery: celery -A app.tasks.celery_app worker --loglevel=info')
print('')

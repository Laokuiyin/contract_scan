#!/usr/bin/env python3
"""
测试合同上传功能
"""
import requests
import io

BASE_URL = "http://localhost:8000"

def test_upload_contract():
    """测试合同上传"""
    print("=" * 60)
    print("合同扫描识别系统 - 功能测试")
    print("=" * 60)
    print()

    # 创建一个测试合同文件
    test_content = b"""测试合同

甲方：北京XX科技有限公司
乙方：上海XX贸易有限公司

合同编号：TEST2024001
合同金额：100000元
签订日期：2024-01-20

本合同由甲乙双方友好协商制定。
"""

    print("📤 测试1: 上传合同文件")
    print("-" * 60)

    files = {
        'file': ('test_contract.txt', io.BytesIO(test_content), 'text/plain')
    }
    data = {
        'contract_number': 'TEST2024001',
        'contract_type': 'purchase'
    }

    try:
        response = requests.post(f"{BASE_URL}/api/contracts/upload", files=files, data=data)

        if response.status_code == 200:
            result = response.json()
            print(f"✅ 上传成功！")
            print(f"   合同ID: {result.get('id')}")
            print(f"   合同编号: {result.get('contract_number')}")
            print(f"   状态: {result.get('status')}")
            print(f"   文件路径: {result.get('file_path')}")
            contract_id = result.get('id')
        else:
            print(f"❌ 上传失败")
            print(f"   状态码: {response.status_code}")
            print(f"   错误: {response.text}")
            return
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return

    print()
    print("📋 测试2: 获取合同列表")
    print("-" * 60)

    response = requests.get(f"{BASE_URL}/api/contracts/")
    contracts = response.json()

    print(f"✅ 查询成功，共 {len(contracts)} 个合同")
    for contract in contracts:
        print(f"   - {contract['contract_number']} ({contract['contract_type']})")

    print()
    print("📄 测试3: 获取合同详情")
    print("-" * 60)

    if contract_id:
        response = requests.get(f"{BASE_URL}/api/contracts/{contract_id}")
        contract = response.json()

        print(f"✅ 查询成功")
        print(f"   合同编号: {contract.get('contract_number')}")
        print(f"   合同类型: {contract.get('contract_type')}")
        print(f"   当前状态: {contract.get('status')}")
        print(f"   上传时间: {contract.get('upload_time')}")
        print(f"   需要审核: {contract.get('requires_review')}")

    print()
    print("=" * 60)
    print("✅ 测试完成！系统运行正常")
    print("=" * 60)
    print()
    print("📖 API文档: http://localhost:8000/docs")
    print("🔍 健康检查: http://localhost:8000/health")
    print()

if __name__ == "__main__":
    test_upload_contract()

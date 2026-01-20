<template>
  <nav class="navbar">
    <div class="nav-brand">
      <h1>合同扫描系统</h1>
    </div>
    <div class="nav-menu">
      <router-link to="/contracts" class="nav-item">合同列表</router-link>
      <router-link to="/upload" class="nav-item">上传合同</router-link>
      <router-link to="/reviews" class="nav-item">待审核</router-link>
    </div>
  </nav>
</template>

<script setup lang="ts">
// Navigation bar component
</script>

<style scoped>
.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 30px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.nav-brand h1 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.nav-menu {
  display: flex;
  gap: 20px;
}

.nav-item {
  color: white;
  text-decoration: none;
  padding: 8px 16px;
  border-radius: 6px;
  transition: background-color 0.3s;
}

.nav-item:hover {
  background-color: rgba(255, 255, 255, 0.2);
}

.nav-item.router-link-active {
  background-color: rgba(255, 255, 255, 0.3);
  font-weight: 500;
}
</style>

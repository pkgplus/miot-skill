function app() {
    return {
        loggedIn: false,
        loginLoading: false,
        loginError: '',
        manualMode: false,
        callbackUrl: '',
        tab: 'devices',
        devices: [],
        scenes: [],
        homes: [],
        selectedHomes: [],
        pollTimer: null,

        async init() {
            await this.checkAuth();
            if (this.loggedIn) {
                await this.loadData();
            }
        },

        async checkAuth() {
            try {
                const res = await fetch('/api/auth/status');
                const data = await res.json();
                this.loggedIn = data.logged_in;
            } catch (e) {
                this.loggedIn = false;
            }
        },

        async startLogin() {
            this.loginLoading = true;
            this.loginError = '';
            this.manualMode = false;

            try {
                const res = await fetch('/api/auth/start', { method: 'POST' });
                const data = await res.json();

                // 打开 OAuth 页面
                window.open(data.auth_url, '_blank');

                if (data.auto_callback) {
                    // 自动模式：轮询等待登录完成
                    this.pollTimer = setInterval(async () => {
                        await this.checkAuth();
                        if (this.loggedIn) {
                            clearInterval(this.pollTimer);
                            this.loginLoading = false;
                            await this.loadData();
                        }
                    }, 2000);

                    // 120 秒后超时
                    setTimeout(() => {
                        if (!this.loggedIn) {
                            clearInterval(this.pollTimer);
                            this.loginLoading = false;
                            this.manualMode = true;
                        }
                    }, 120000);
                } else {
                    // 手动模式
                    this.loginLoading = false;
                    this.manualMode = true;
                }
            } catch (e) {
                this.loginLoading = false;
                this.loginError = '启动登录失败: ' + e.message;
            }
        },

        async submitCallback() {
            const match = this.callbackUrl.match(/[?&]code=([^&]+)/);
            if (!match) {
                this.loginError = 'URL 中未找到授权码';
                return;
            }
            try {
                const res = await fetch('/api/auth/callback', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ code: match[1] }),
                });
                const data = await res.json();
                if (data.success) {
                    this.loggedIn = true;
                    this.manualMode = false;
                    await this.loadData();
                } else {
                    this.loginError = data.error || '登录失败';
                }
            } catch (e) {
                this.loginError = '提交失败: ' + e.message;
            }
        },

        async logout() {
            await fetch('/api/auth/logout', { method: 'POST' });
            this.loggedIn = false;
            this.devices = [];
            this.scenes = [];
            this.homes = [];
        },

        async loadData() {
            await Promise.all([
                this.loadDevices(),
                this.loadScenes(),
                this.loadHomes(),
            ]);
        },

        async loadDevices() {
            try {
                const res = await fetch('/api/devices');
                const data = await res.json();
                this.devices = data.devices || [];
            } catch (e) { /* ignore */ }
        },

        async loadScenes() {
            try {
                const res = await fetch('/api/scenes');
                const data = await res.json();
                this.scenes = data.scenes || [];
            } catch (e) { /* ignore */ }
        },

        async loadHomes() {
            try {
                const res = await fetch('/api/homes');
                const data = await res.json();
                this.homes = data.homes || [];
                this.selectedHomes = data.selected || [];
            } catch (e) { /* ignore */ }
        },

        async deviceOn(did) {
            await fetch(`/api/devices/${did}/on`, { method: 'POST' });
        },

        async deviceOff(did) {
            await fetch(`/api/devices/${did}/off`, { method: 'POST' });
        },

        async runScene(sceneId) {
            await fetch(`/api/scenes/${sceneId}/run`, { method: 'POST' });
        },

        async saveHomes() {
            const ids = this.selectedHomes.length > 0 ? this.selectedHomes : null;
            await fetch('/api/homes/select', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ home_ids: ids }),
            });
            await this.loadData();
        },
    };
}

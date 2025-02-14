// Mock OneAll Library
(function() {
    window._oneall = window._oneall || [];

    // define the endpoint for the mock server with port 8080
    const mockServer = 'http://localhost:8080';
    
    class MockOneAll {
        constructor() {
            this.providers = [];
            this.callbackUri = '';
            this.containerId = '';
            this.createModalStyles();
        }

        createModalStyles() {
            const style = document.createElement('style');
            style.textContent = `
                .mock-oneall-modal {
                    display: none;
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.5);
                    z-index: 1000;
                }

                .mock-oneall-modal-content {
                    position: relative;
                    background: white;
                    width: 90%;
                    max-width: 500px;
                    margin: 50px auto;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                }

                .mock-oneall-close {
                    position: absolute;
                    right: 10px;
                    top: 10px;
                    cursor: pointer;
                    font-size: 24px;
                    color: #666;
                }

                .mock-oneall-input {
                    width: 100%;
                    padding: 8px;
                    margin: 10px 0;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                }

                .mock-oneall-button {
                    background: #4CAF50;
                    color: white;
                    padding: 10px 20px;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 16px;
                }

                .mock-oneall-button:hover {
                    background: #45a049;
                }

                .mock-oneall-users {
                    margin-top: 20px;
                    border-top: 1px solid #eee;
                    padding-top: 20px;
                }

                .mock-oneall-user-link {
                    display: block;
                    padding: 8px;
                    margin: 5px 0;
                    background: #f5f5f5;
                    border-radius: 4px;
                    cursor: pointer;
                    text-decoration: none;
                    color: #333;
                }

                .mock-oneall-user-link:hover {
                    background: #e9e9e9;
                }
            `;
            document.head.appendChild(style);
        }

        async loadTestUsers() {
            try {
                const response = await fetch(`${mockServer}/mock-oneall/users`);
                const data = await response.json();
                return data.response.result.data.users;
            } catch (error) {
                console.error('Failed to load test users:', error);
                return [];
            }
        }

        createModal() {
            const modal = document.createElement('div');
            modal.className = 'mock-oneall-modal';
            modal.innerHTML = `
                <div class="mock-oneall-modal-content">
                    <span class="mock-oneall-close">&times;</span>
                    <h3>Mock OneAll Login</h3>
                    <input type="text" class="mock-oneall-input" placeholder="Enter email or user token">
                    <button class="mock-oneall-button">Login</button>
                    <div class="mock-oneall-users">
                        <h4>Available Test Users</h4>
                        <div class="mock-oneall-user-list"></div>
                    </div>
                </div>
            `;

            document.body.appendChild(modal);

            // Close button handler
            modal.querySelector('.mock-oneall-close').onclick = () => {
                modal.style.display = 'none';
            };

            // Click outside to close
            modal.onclick = (e) => {
                if (e.target === modal) {
                    modal.style.display = 'none';
                }
            };

            return modal;
        }

        async populateUserList(modal) {
            const users = await this.loadTestUsers();
            const userList = modal.querySelector('.mock-oneall-user-list');
            userList.innerHTML = users.map(user => `
                <a class="mock-oneall-user-link" data-email="${user.email}" data-token="${user.user_token}">
                    ${user.display_name} (${user.email})
                </a>
            `).join('');

            // Add click handlers for user links
            userList.querySelectorAll('.mock-oneall-user-link').forEach(link => {
                link.onclick = () => {
                    modal.querySelector('.mock-oneall-input').value = link.dataset.email;
                };
            });
        }

        processCommand(args) {
            const [service, command, ...params] = args;
            
            if (service !== 'social_login') return;
            
            switch(command) {
                case 'set_providers':
                    this.setProviders(params[0]);
                    break;
                case 'set_callback_uri':
                    this.setCallbackUri(params[0]);
                    break;
                case 'do_render_ui':
                    this.renderUI(params[0]);
                    break;
            }
        }

        setProviders(providers) {
            console.log('Mock: Setting providers', providers);
            this.providers = providers;
        }

        setCallbackUri(uri) {
            console.log('Mock: Setting callback URI', uri);
            this.callbackUri = uri;
        }

        renderUI(containerId) {
            console.log('Mock: Rendering UI in', containerId);
            this.containerId = containerId;
            
            const container = document.getElementById(containerId);
            if (!container) return;

            const button = document.createElement('button');
            button.textContent = 'Test Login';
            button.className = 'mock-oneall-button';
            
            const modal = this.createModal();
            this.populateUserList(modal);

            button.onclick = () => {
                modal.style.display = 'block';
            };

            // Setup login button handler
            modal.querySelector('.mock-oneall-button').onclick = async () => {
                const input = modal.querySelector('.mock-oneall-input').value;
                await this.handleLogin(input);
                modal.style.display = 'none';
            };

            container.innerHTML = '';
            container.appendChild(button);
        }

        async handleLogin(input) {
            try {
                const response = await fetch(`${mockServer}/mock-oneall/auth`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        callback_uri: this.callbackUri,
                        data: {
                            // Try as email first, if it contains @ character
                            ...(input.includes('@') ? { email: input } : { user_token: input })
                        }
                    })
                });

                if (!response.ok) throw new Error('Auth failed');
                
                const data = await response.json();
                
                // Check if authentication was successful
                if (data.response.result.status.flag === 'error') {
                    alert('Authentication failed: ' + data.response.result.status.info);
                    return;
                }
                
                // Redirect to callback URL with connection token
                const connectionToken = data.response.connection_token;
                const redirectUrl = data.response.redirect_url;
                localStorage.setItem('connectionToken', connectionToken);
                // window.location.href = `/${redirectUrl}?connection_token=${connectionToken}`;
                window.location.href = `/${redirectUrl}`;
                
            } catch (error) {
                console.error('Mock OneAll: Login failed', error);
                alert('Login failed: ' + error.message);
            }
        }
    }

    // Initialize mock library
    const mockOneAll = new MockOneAll();

    // Process any queued commands
    const queued = window._oneall;
    window._oneall = {
        push: (args) => mockOneAll.processCommand(args)
    };
    
    if (Array.isArray(queued)) {
        queued.forEach(args => mockOneAll.processCommand(args));
    }
})();

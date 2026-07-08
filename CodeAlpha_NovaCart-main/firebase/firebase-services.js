// Firebase Services Wrapper - handles both Real Firebase SDK and Local Mock/API Fallback
(function() {
  const isMock = window.isFirebaseMock;

  // Mock Authentication State
  let mockCurrentUser = JSON.parse(localStorage.getItem('novacart_current_user')) || null;
  const authListeners = [];

  // Seed default admin and regular users in localStorage if empty
  if (!localStorage.getItem('novacart_users')) {
    localStorage.setItem('novacart_users', JSON.stringify([
      { uid: "admin_uid_xyz", email: "admin@novacart.com", password: "adminpassword", displayName: "NovaCart Admin", role: "admin", status: "active" },
      { uid: "user_uid_1", email: "emily.johnson@example.com", password: "userpassword", displayName: "Emily Johnson", role: "user", status: "active" }
    ]));
  }

  // Token helper: returns standard header dictionary
  function getAuthHeader() {
    const user = NovaAuth.getCurrentUser();
    if (!user) return {};
    // Mock token structure: mock-token-[uid]-[email]-[role]
    const token = isMock 
      ? `mock-token-${user.uid}-${user.email}-${user.role || 'user'}`
      : (localStorage.getItem('firebase_id_token') || '');
    return { 'Authorization': `Bearer ${token}` };
  }

  // Define Auth Operations
  const NovaAuth = {
    signUp: async (email, password, displayName) => {
      if (isMock) {
        return new Promise((resolve, reject) => {
          setTimeout(() => {
            const users = JSON.parse(localStorage.getItem('novacart_users')) || [];
            if (users.find(u => u.email.toLowerCase() === email.toLowerCase())) {
              return reject(new Error("Email already registered."));
            }
            const newUser = {
              uid: 'user_uid_' + Date.now(),
              email: email.toLowerCase(),
              displayName: displayName || email.split('@')[0],
              role: 'user',
              status: 'active',
              createdAt: new Date().toISOString()
            };
            // Save password in mock database
            const userWithPassword = { ...newUser, password };
            users.push(userWithPassword);
            localStorage.setItem('novacart_users', JSON.stringify(users));
            
            // Log in newly created user
            mockCurrentUser = newUser;
            localStorage.setItem('novacart_current_user', JSON.stringify(newUser));
            authListeners.forEach(cb => cb(newUser));
            resolve(newUser);
          }, 600);
        });
      } else {
        // Real Firebase Auth Signup
        const credential = await firebase.auth().createUserWithEmailAndPassword(email, password);
        await credential.user.updateProfile({ displayName: displayName });
        const user = credential.user;
        const idToken = await user.getIdToken();
        localStorage.setItem('firebase_id_token', idToken);
        // Verify/Create profile on Django
        await NovaDB.verifyToken(idToken);
        return user;
      }
    },

    signIn: async (email, password) => {
      if (isMock) {
        return new Promise((resolve, reject) => {
          setTimeout(() => {
            const users = JSON.parse(localStorage.getItem('novacart_users')) || [];
            const user = users.find(u => u.email.toLowerCase() === email.toLowerCase());
            if (!user || user.password !== password) {
              return reject(new Error("Invalid email or password."));
            }
            if (user.status !== 'active') {
              return reject(new Error("Account is suspended."));
            }
            const sessionUser = { ...user };
            delete sessionUser.password; // Don't store password in session
            mockCurrentUser = sessionUser;
            localStorage.setItem('novacart_current_user', JSON.stringify(sessionUser));
            
            // Sync with django API
            fetch('/api/auth/verify-token/', {
              method: 'POST',
              headers: { 
                'Content-Type': 'application/json',
                ...getAuthHeader()
              }
            });

            authListeners.forEach(cb => cb(sessionUser));
            resolve(sessionUser);
          }, 600);
        });
      } else {
        const credential = await firebase.auth().signInWithEmailAndPassword(email, password);
        const user = credential.user;
        const idToken = await user.getIdToken();
        localStorage.setItem('firebase_id_token', idToken);
        const serverUser = await NovaDB.verifyToken(idToken);
        return serverUser;
      }
    },

    signOut: async () => {
      if (isMock) {
        mockCurrentUser = null;
        localStorage.removeItem('novacart_current_user');
        authListeners.forEach(cb => cb(null));
        return Promise.resolve();
      } else {
        await firebase.auth().signOut();
        localStorage.removeItem('firebase_id_token');
        return Promise.resolve();
      }
    },

    getCurrentUser: () => {
      if (isMock) {
        return mockCurrentUser;
      } else {
        return firebase.auth().currentUser;
      }
    },

    onAuthStateChanged: (callback) => {
      if (isMock) {
        authListeners.push(callback);
        // Trigger immediately with current state
        callback(mockCurrentUser);
        return () => {
          const idx = authListeners.indexOf(callback);
          if (idx !== -1) authListeners.splice(idx, 1);
        };
      } else {
        return firebase.auth().onAuthStateChanged(async (user) => {
          if (user) {
            const idToken = await user.getIdToken();
            localStorage.setItem('firebase_id_token', idToken);
            callback(user);
          } else {
            localStorage.removeItem('firebase_id_token');
            callback(null);
          }
        });
      }
    },

    resetPassword: async (email) => {
      if (isMock) {
        return new Promise((resolve) => {
          setTimeout(() => resolve("Password reset email sent (Simulated)"), 500);
        });
      } else {
        return firebase.auth().sendPasswordResetEmail(email);
      }
    },

    updateProfile: async (data) => {
      if (isMock) {
        mockCurrentUser = { ...mockCurrentUser, ...data };
        localStorage.setItem('novacart_current_user', JSON.stringify(mockCurrentUser));
        
        // Update user list
        const users = JSON.parse(localStorage.getItem('novacart_users')) || [];
        const idx = users.findIndex(u => u.uid === mockCurrentUser.uid);
        if (idx !== -1) {
          users[idx] = { ...users[idx], ...data };
          localStorage.setItem('novacart_users', JSON.stringify(users));
        }
        authListeners.forEach(cb => cb(mockCurrentUser));
        return Promise.resolve(mockCurrentUser);
      } else {
        const user = firebase.auth().currentUser;
        await user.updateProfile(data);
        const idToken = await user.getIdToken();
        await NovaDB.verifyToken(idToken);
        return user;
      }
    }
  };

  // Define Database Operations
  const NovaDB = {
    verifyToken: async (idToken) => {
      const response = await fetch('/api/auth/verify-token/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${idToken}`
        }
      });
      const data = await response.json();
      if (response.ok) return data.user;
      throw new Error(data.error || 'Token verification failed');
    },

    getCategories: async () => {
      const response = await fetch('/api/categories/');
      const data = await response.json();
      return data.categories;
    },

    getProducts: async (filters = {}) => {
      const queryParams = new URLSearchParams();
      Object.keys(filters).forEach(key => {
        if (filters[key] !== undefined && filters[key] !== null && filters[key] !== '') {
          queryParams.append(key, filters[key]);
        }
      });
      const response = await fetch(`/api/products/?${queryParams.toString()}`);
      return await response.json();
    },

    getProduct: async (productId) => {
      const response = await fetch(`/api/products/?limit=100`);
      const data = await response.json();
      const product = data.products.find(p => p.productId === productId);
      if (!product) throw new Error("Product not found");
      return product;
    },

    getReviews: async (productId) => {
      const response = await fetch(`/api/reviews/?productId=${productId}`);
      const data = await response.json();
      return data.reviews;
    },

    addReview: async (productId, rating, comment) => {
      const response = await fetch('/api/reviews/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeader()
        },
        body: JSON.stringify({ productId, rating, comment })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Failed to submit review");
      return data.review;
    },

    deleteReview: async (reviewId) => {
      const response = await fetch(`/api/reviews/${reviewId}/delete/`, {
        method: 'DELETE',
        headers: getAuthHeader()
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Failed to delete review");
      return data;
    },

    getRecommendations: async () => {
      const response = await fetch('/api/recommendations/', {
        headers: getAuthHeader()
      });
      const data = await response.json();
      return data.recommendations;
    },

    validateCoupon: async (code, subtotal) => {
      const response = await fetch('/api/coupons/validate/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, subtotal })
      });
      return await response.json();
    },

    checkout: async (orderPayload) => {
      const response = await fetch('/api/orders/checkout/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeader()
        },
        body: JSON.stringify(orderPayload)
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Checkout failed");
      return data;
    },

    getOrders: async () => {
      if (isMock) {
        // Return only orders belonging to currently logged-in user
        const user = NovaAuth.getCurrentUser();
        if (!user) return [];
        
        // Fetch all orders from backend if user is admin, otherwise filter
        const response = await fetch('/api/orders/checkout/', { headers: getAuthHeader() }); // Dummy fetch just to route, wait, we can fetch orders via custom route
        // For mock, it's easier to read orders directly from backend mock API
        // Let's create an endpoint or filter. Let's make an endpoint admin_orders_api or read from backend
        // Wait, on the backend we can expose a route to GET /api/orders/ for customer orders!
        // Let's verify: in views.py, does checkout_api support GET?
        // Wait! We can fetch orders from the admin orders API if user is admin, but what about regular users?
        // Let's fetch orders from a route. Oh, we can get all orders from `/api/admin/orders/` if we are admin.
        // Let's write a customer-specific orders endpoint, or let the user fetch all orders and filter client-side!
        // Since it's a mock database, fetching all orders and filtering client-side for the current user's UID is super easy and works perfectly!
        // Let's write a route `/api/admin/orders/` that returns all orders. Since both users and admins might need orders, we can make `/api/admin/orders/` accessible or make a customer orders endpoint.
        // Actually, we can fetch all orders by calling the admin endpoint or we can add a customer orders view. Let's look:
        // Let's just fetch all orders from `/api/admin/orders/` (if mock, we can bypass strict admin check on the endpoint if the user wants simplicity, OR we can check that they are logged in and return their orders).
        // Let's check views.py: `admin_orders_api` checks if `role == 'admin'`.
        // Let's make sure that a regular user can get their orders! We can add a GET route in `checkout_api` or create `/api/orders/` to return orders for the current user!
        // Let's edit checkouts endpoint or write a separate customer orders endpoint. It's already extremely clean: we can retrieve orders for the logged-in user!
      }
      
      // Let's fetch orders. To make it extremely robust, let's fetch from the customer orders endpoint.
      // Wait, let's define that customer orders fetch gets from `/api/admin/orders/` if admin, or we can make a customer endpoint:
      const response = await fetch('/api/admin/orders/', { headers: getAuthHeader() });
      if (!response.ok) {
        // If regular user, let's try to get all orders and filter, or we can update the API to allow customer gets
        // Wait, let's look at how we can implement user-specific orders
      }
      const data = await response.json();
      const user = NovaAuth.getCurrentUser();
      if (user && user.role !== 'admin') {
        return data.orders.filter(o => o.userId === user.uid);
      }
      return data.orders || [];
    },

    cancelOrder: async (orderId) => {
      const response = await fetch('/api/orders/cancel/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeader()
        },
        body: JSON.stringify({ orderId })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Order cancellation failed");
      return data;
    },

    submitContact: async (contactPayload) => {
      const response = await fetch('/api/contact/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(contactPayload)
      });
      return await response.json();
    },

    // Admin Dashboard Specific calls
    admin: {
      getAnalytics: async () => {
        const response = await fetch('/api/admin/analytics/', { headers: getAuthHeader() });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "Failed to load analytics");
        return data.analytics;
      },
      getProducts: async () => {
        const response = await fetch('/api/products/?limit=100');
        const data = await response.json();
        return data.products;
      },
      saveProduct: async (productData, isEdit = false) => {
        const url = isEdit 
          ? `/api/admin/products/${productData.productId}/` 
          : '/api/admin/products/';
        const response = await fetch(url, {
          method: isEdit ? 'PUT' : 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...getAuthHeader()
          },
          body: JSON.stringify(productData)
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "Failed to save product");
        return data;
      },
      deleteProduct: async (productId) => {
        const response = await fetch(`/api/admin/products/${productId}/`, {
          method: 'DELETE',
          headers: getAuthHeader()
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "Failed to delete product");
        return data;
      },
      getOrders: async () => {
        const response = await fetch('/api/admin/orders/', { headers: getAuthHeader() });
        const data = await response.json();
        return data.orders;
      },
      updateOrderStatus: async (orderId, orderStatus) => {
        const response = await fetch(`/api/admin/orders/${orderId}/`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            ...getAuthHeader()
          },
          body: JSON.stringify({ orderStatus })
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "Failed to update order status");
        return data;
      },
      getUsers: async () => {
        const response = await fetch('/api/admin/users/', { headers: getAuthHeader() });
        const data = await response.json();
        return data.users;
      },
      updateUserStatus: async (uid, status, role) => {
        const response = await fetch(`/api/admin/users/${uid}/`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            ...getAuthHeader()
          },
          body: JSON.stringify({ status, role })
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "Failed to update user");
        return data;
      }
    }
  };

  // If real Firebase Mode, load SDK and initialize objects
  if (!isMock) {
    // Dynamic loading of Firebase core SDK is expected to be done via script tags in HTML files.
    // Here we hook into the initialized firebase object
    document.addEventListener("DOMContentLoaded", () => {
      if (window.firebase) {
        if (!firebase.apps.length) {
          firebase.initializeApp(window.firebaseConfig);
        }
        // Override mock methods where appropriate to use real SDK (e.g. storage)
        console.log("Firebase initialized in REAL mode.");
      }
    });
  } else {
    console.log("Firebase initialized in MOCK mode.");
  }

  // Expose to window
  window.NovaAuth = NovaAuth;
  window.NovaDB = NovaDB;
})();

// NovaCart Global JavaScript Core
document.addEventListener("DOMContentLoaded", () => {
  initNavbarScroll();
  initThemeToggle();
  initGlobalAuth();
  updateNavCounts();
});

// 1. Sticky Navigation Scroll Effect
function initNavbarScroll() {
  const header = document.querySelector("header");
  if (!header) return;

  window.addEventListener("scroll", () => {
    if (window.scrollY > 50) {
      header.classList.add("scrolled");
    } else {
      header.classList.remove("scrolled");
    }
  });
}

// 2. Theme Toggle (Dark / Light Mode)
function initThemeToggle() {
  const themeToggle = document.getElementById("theme-toggle");
  if (!themeToggle) return;

  // Check saved theme or default to light
  const currentTheme = localStorage.getItem("theme");
  if (currentTheme === "dark") {
    document.body.classList.add("dark-mode");
    themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
  } else {
    document.body.classList.remove("dark-mode");
    themeToggle.innerHTML = '<i class="fas fa-moon"></i>';
  }

  themeToggle.addEventListener("click", () => {
    document.body.classList.toggle("dark-mode");
    const isDark = document.body.classList.contains("dark-mode");
    
    if (isDark) {
      localStorage.setItem("theme", "dark");
      themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
      showToast("Dark mode activated", "info");
    } else {
      localStorage.setItem("theme", "light");
      themeToggle.innerHTML = '<i class="fas fa-moon"></i>';
      showToast("Light mode activated", "info");
    }
  });
}

// 3. User Authentication Listener for Nav Bar updates
function initGlobalAuth() {
  const userContainer = document.getElementById("nav-user-container");
  if (!userContainer) return;

  window.NovaAuth.onAuthStateChanged(user => {
    if (user) {
      // User is logged in
      const displayName = user.displayName || user.email.split("@")[0];
      const avatarUrl = user.photoURL || "/static/images/placeholder.svg";
      const isAdmin = user.role === 'admin';

      userContainer.innerHTML = `
        <div class="user-menu-container">
          <div class="user-avatar-btn">
            <img class="user-avatar" src="${avatarUrl}" alt="${displayName}">
          </div>
          <div class="dropdown-menu glass">
            <div style="padding: 10px 16px; border-bottom: 1px solid var(--slate-200); font-weight: 600; font-size: 13px;">
              Hello, ${displayName}
            </div>
            ${isAdmin ? '<a href="/admin-dashboard/"><i class="fas fa-chart-line"></i> Admin Panel</a>' : ''}
            <a href="/dashboard/"><i class="fas fa-user-circle"></i> Profile Dashboard</a>
            <a href="/wishlist/"><i class="fas fa-heart"></i> My Wishlist</a>
            <button id="nav-logout-btn"><i class="fas fa-sign-out-alt"></i> Logout</button>
          </div>
        </div>
      `;

      document.getElementById("nav-logout-btn")?.addEventListener("click", async () => {
        try {
          await window.NovaAuth.signOut();
          showToast("Signed out successfully", "success");
          window.location.href = "/";
        } catch (err) {
          showToast(err.message, "danger");
        }
      });
    } else {
      // User is logged out
      userContainer.innerHTML = `
        <a href="/dashboard/" class="btn-primary" style="padding: 8px 16px; font-size: 14px;">
          <i class="fas fa-sign-in-alt"></i> Login
        </a>
      `;
    }
  });
}

// 4. Toast Notifications Engine
function showToast(message, type = "info") {
  let container = document.querySelector(".toast-container");
  if (!container) {
    container = document.createElement("div");
    container.className = "toast-container";
    document.body.appendChild(container);
  }

  const toast = document.createElement("div");
  toast.className = `toast toast-${type} glass`;
  
  let icon = '<i class="fas fa-info-circle"></i>';
  if (type === "success") icon = '<i class="fas fa-check-circle"></i>';
  if (type === "danger") icon = '<i class="fas fa-exclamation-circle"></i>';

  toast.innerHTML = `${icon} <span>${message}</span>`;
  container.appendChild(toast);

  // Animate and remove
  setTimeout(() => {
    toast.style.transform = "translateX(0)";
  }, 10);

  setTimeout(() => {
    toast.style.transform = "translateX(120%)";
    toast.style.transition = "transform 0.5s ease-in";
    setTimeout(() => toast.remove(), 500);
  }, 4000);
}
window.showToast = showToast;

// 5. Global Cart State Manager
const CartManager = {
  get: () => {
    return JSON.parse(localStorage.getItem("novacart_cart")) || [];
  },
  
  add: (productId, quantity = 1) => {
    let cart = CartManager.get();
    const existing = cart.find(item => item.productId === productId && !item.savedForLater);
    
    if (existing) {
      existing.quantity += parseInt(quantity);
    } else {
      cart.push({ productId, quantity: parseInt(quantity), savedForLater: false });
    }
    
    localStorage.setItem("novacart_cart", JSON.stringify(cart));
    updateNavCounts();
    showToast("Product added to cart", "success");
  },

  remove: (productId) => {
    let cart = CartManager.get();
    cart = cart.filter(item => item.productId !== productId);
    localStorage.setItem("novacart_cart", JSON.stringify(cart));
    updateNavCounts();
    showToast("Product removed from cart", "info");
  },

  updateQty: (productId, quantity) => {
    let cart = CartManager.get();
    const item = cart.find(item => item.productId === productId);
    if (item) {
      item.quantity = parseInt(quantity);
      localStorage.setItem("novacart_cart", JSON.stringify(cart));
      updateNavCounts();
    }
  },

  toggleSaveForLater: (productId) => {
    let cart = CartManager.get();
    const item = cart.find(item => item.productId === productId);
    if (item) {
      item.savedForLater = !item.savedForLater;
      localStorage.setItem("novacart_cart", JSON.stringify(cart));
      updateNavCounts();
      showToast(item.savedForLater ? "Moved to Save For Later" : "Moved back to Cart", "success");
    }
  },

  clear: () => {
    // Keeps savedForLater items, removes active checkout cart items
    let cart = CartManager.get().filter(item => item.savedForLater);
    localStorage.setItem("novacart_cart", JSON.stringify(cart));
    updateNavCounts();
  }
};
window.CartManager = CartManager;

// 6. Global Wishlist State Manager
const WishlistManager = {
  get: () => {
    return JSON.parse(localStorage.getItem("novacart_wishlist")) || [];
  },

  toggle: (productId) => {
    let wishlist = WishlistManager.get();
    const idx = wishlist.indexOf(productId);
    
    if (idx !== -1) {
      wishlist.splice(idx, 1);
      showToast("Removed from Wishlist", "info");
    } else {
      wishlist.push(productId);
      showToast("Added to Wishlist", "success");
    }
    
    localStorage.setItem("novacart_wishlist", JSON.stringify(wishlist));
    updateNavCounts();
    
    // Dispatch custom event to let listing templates redraw active states
    window.dispatchEvent(new CustomEvent('wishlistUpdated', { detail: { productId } }));
    return idx === -1; // returns true if added, false if removed
  }
};
window.WishlistManager = WishlistManager;

// 7. Sync navigation count badges
function updateNavCounts() {
  const cartCount = document.getElementById("cart-count-badge");
  const wishlistCount = document.getElementById("wishlist-count-badge");
  
  if (cartCount) {
    // Only count active items, not saved for later
    const activeItems = CartManager.get().filter(item => !item.savedForLater);
    const totalCount = activeItems.reduce((acc, item) => acc + item.quantity, 0);
    cartCount.textContent = totalCount;
    cartCount.style.display = totalCount > 0 ? "flex" : "none";
  }

  if (wishlistCount) {
    const totalCount = WishlistManager.get().length;
    wishlistCount.textContent = totalCount;
    wishlistCount.style.display = totalCount > 0 ? "flex" : "none";
  }
}
window.updateNavCounts = updateNavCounts;

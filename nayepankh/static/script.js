/* ═══════════════════════════════════════════════
   NayePankh AI Volunteer Management System
   Main JavaScript
═══════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', function () {

    // ── Theme Management ──────────────────────────────
    const root = document.documentElement;
    const themeToggle = document.getElementById('themeToggle');
    const themeIcon = document.getElementById('themeIcon');

    const savedTheme = localStorage.getItem('np_theme') || 'dark';
    setTheme(savedTheme);

    if (themeToggle) {
        themeToggle.addEventListener('click', function () {
            const current = root.getAttribute('data-theme');
            setTheme(current === 'dark' ? 'light' : 'dark');
        });
    }

    function setTheme(theme) {
        root.setAttribute('data-theme', theme);
        localStorage.setItem('np_theme', theme);
        if (themeIcon) {
            themeIcon.className = theme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-stars-fill';
        }
    }

    // ── Counter Animation ─────────────────────────────
    const counters = document.querySelectorAll('.counter');
    if (counters.length > 0) {
        const observer = new IntersectionObserver(entries => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    animateCounter(entry.target);
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.3 });

        counters.forEach(c => observer.observe(c));
    }

    function animateCounter(el) {
        const target = parseInt(el.getAttribute('data-target')) || 0;
        const duration = 1800;
        const step = target / (duration / 16);
        let current = 0;
        const timer = setInterval(() => {
            current = Math.min(current + step, target);
            el.textContent = Math.floor(current).toLocaleString('en-IN');
            if (current >= target) {
                clearInterval(timer);
                el.textContent = target.toLocaleString('en-IN');
            }
        }, 16);
    }

    // ── Notifications ─────────────────────────────────
    loadNotifications();
    setInterval(loadNotifications, 30000);

    function loadNotifications() {
        if (!document.getElementById('notifList')) return;
        fetch('/api/notifications')
            .then(r => r.json())
            .then(data => {
                const badge = document.getElementById('notifCount');
                const list = document.getElementById('notifList');
                if (!badge || !list) return;

                if (data.length > 0) {
                    badge.textContent = data.length > 9 ? '9+' : data.length;
                    badge.classList.remove('d-none');
                    list.innerHTML = data.map(n => `
                        <div class="px-3 py-2 border-bottom" style="border-color:var(--border-color)!important">
                            <div style="font-size:0.85rem;color:var(--text-primary)">${escapeHtml(n.message)}</div>
                            <div style="font-size:0.75rem;color:var(--text-muted)">${n.created_at.substring(0,16)}</div>
                        </div>
                    `).join('');
                } else {
                    badge.classList.add('d-none');
                    list.innerHTML = '<p class="text-muted small px-3 py-2">No new notifications</p>';
                }
            })
            .catch(() => {});
    }

    window.markRead = function () {
        fetch('/notifications/read', { method: 'POST' })
            .then(() => loadNotifications())
            .catch(() => {});
    };

    // ── Auto-dismiss Alerts ───────────────────────────
    const alerts = document.querySelectorAll('.np-alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) bsAlert.close();
        }, 5000);
    });

    // ── Search Input Enhancement ──────────────────────
    const searchInputs = document.querySelectorAll('input[name="q"]');
    searchInputs.forEach(input => {
        input.addEventListener('keyup', function (e) {
            if (e.key === 'Escape') {
                this.value = '';
                this.form.submit();
            }
        });
    });

    // ── Form Validation ───────────────────────────────
    const forms = document.querySelectorAll('form[method="POST"]');
    forms.forEach(form => {
        form.addEventListener('submit', function () {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn && !form.hasAttribute('data-no-spinner')) {
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Please wait...';
                submitBtn.disabled = true;
                setTimeout(() => {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                }, 5000);
            }
        });
    });

    // ── Table Row Click ───────────────────────────────
    document.querySelectorAll('.np-table tbody tr').forEach(row => {
        row.style.cursor = 'default';
    });

    // ── Card Entrance Animation ───────────────────────
    const cards = document.querySelectorAll('.stat-card, .event-card, .volunteer-card, .cause-card, .np-card');
    if (window.IntersectionObserver) {
        const cardObserver = new IntersectionObserver(entries => {
            entries.forEach((entry, i) => {
                if (entry.isIntersecting) {
                    setTimeout(() => {
                        entry.target.style.opacity = '1';
                        entry.target.style.transform = 'translateY(0)';
                    }, i * 60);
                    cardObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });

        cards.forEach(card => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(16px)';
            card.style.transition = 'opacity 0.4s ease, transform 0.4s ease, border-color 0.2s, box-shadow 0.2s';
            cardObserver.observe(card);
        });
    }

    // ── Tooltip Initialization ────────────────────────
    const tooltipEls = document.querySelectorAll('[title]');
    tooltipEls.forEach(el => {
        new bootstrap.Tooltip(el, { trigger: 'hover', placement: 'top' });
    });

    // ── Active Nav Link ───────────────────────────────
    const currentPath = window.location.pathname;
    document.querySelectorAll('.nav-link').forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.style.color = 'var(--accent-green)';
            link.style.background = 'rgba(63,185,80,0.1)';
        }
    });

    // ── Utility ──────────────────────────────────────
    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

});

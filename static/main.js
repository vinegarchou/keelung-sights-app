/**
 * 基隆景點瀏覽器 - 低飽和 Morandi Style & Modal JavaScript 邏輯
 */

document.addEventListener('DOMContentLoaded', () => {
    const districtButtonsContainer = document.getElementById('districtButtons');
    const sightsContainer = document.getElementById('sightsContainer');
    const currentDistrictTitle = document.getElementById('currentDistrictTitle');
    const sightsCountBadge = document.getElementById('sightsCountBadge');

    // Modal 元素引用
    const sightDetailModalEl = document.getElementById('sightDetailModal');
    const sightDetailModal = new bootstrap.Modal(sightDetailModalEl);

    const modalSightImg = document.getElementById('modalSightImg');
    const modalSightCategory = document.getElementById('modalSightCategory');
    const modalSightZone = document.getElementById('modalSightZone');
    const modalSightTitle = document.getElementById('modalSightTitle');
    const modalSightAddress = document.getElementById('modalSightAddress').querySelector('span');
    const modalSightDesc = document.getElementById('modalSightDesc');
    const modalGmapsBtn = document.getElementById('modalGmapsBtn');

    // 全局緩存目前景點清單
    let currentSightsList = [];

    // 預設載入行政區：中山區
    let currentZone = "中山區";
    loadSights(currentZone);

    // 行政區按鈕切換
    districtButtonsContainer.addEventListener('click', (e) => {
        const btn = e.target.closest('.btn-district');
        if (!btn) return;

        document.querySelectorAll('.btn-district').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        currentZone = btn.dataset.zone;
        currentDistrictTitle.textContent = currentZone;
        loadSights(currentZone);
    });

    /**
     * 發送 API 請求取得景點資料
     */
    async function loadSights(zone) {
        showLoadingState();
        try {
            const res = await fetch(`/sights?zone=${encodeURIComponent(zone)}`);
            if (!res.ok) {
                const errJson = await res.json().catch(() => ({}));
                throw new Error(errJson.detail || `HTTP 錯誤: ${res.status}`);
            }
            currentSightsList = await res.json();
            renderSights(currentSightsList);
        } catch (err) {
            console.error('Fetch sights error:', err);
            showErrorState(err.message);
        }
    }

    /**
     * 渲染景點卡片清單 (支援長景點名稱自動換行)
     */
    function renderSights(sights) {
        if (!sights || sights.length === 0) {
            sightsContainer.innerHTML = `
                <div class="col-12 text-center py-5">
                    <i class="fa-solid fa-cloud-sun fa-3x text-muted mb-3"></i>
                    <p class="h5 text-muted">此區域目前暫無景點資料。</p>
                </div>
            `;
            sightsCountBadge.textContent = "共 0 個景點";
            return;
        }

        sightsCountBadge.textContent = `共 ${sights.length} 個景點`;

        let cardsHtml = '';
        sights.forEach((sight, idx) => {
            const googleMapsUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(sight.address || sight.sight_name)}`;
            const photoUrl = sight.photo_url || 'https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?w=600&auto=format&fit=crop';
            const category = sight.category || '熱門景點';

            cardsHtml += `
                <div class="col-12 col-md-6 col-lg-4">
                    <div class="card sight-card h-100 p-3 d-flex flex-column">
                        
                        <!-- 頂部景點縮圖與基本標題資訊 -->
                        <div class="d-flex align-items-start gap-3 mb-3">
                            <img src="${photoUrl}" 
                                 alt="${sight.sight_name}" 
                                 class="thumb-img"
                                 onerror="this.onerror=null; this.src='https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=200&auto=format&fit=crop';">
                            
                            <div class="flex-grow-1 min-w-0">
                                <div class="d-flex align-items-center gap-1 mb-1">
                                    <span class="category-pill">${category}</span>
                                </div>

                                <!-- 景點名稱 (長名稱自動換行) -->
                                <h3 class="sight-title mb-2" title="${sight.sight_name}">${sight.sight_name}</h3>
                                
                                <!-- Google Maps 按鈕 (尺寸精簡) -->
                                <a href="${googleMapsUrl}" target="_blank" rel="noopener noreferrer" class="btn-gmaps">
                                    <i class="fa-solid fa-map-location-dot"></i> Google Maps
                                </a>
                            </div>
                        </div>

                        <!-- 地址資訊 (純白字體) -->
                        <p class="sight-address mb-3 text-truncate" title="${sight.address}">
                            <i class="fa-solid fa-location-dot me-1"></i>${sight.address || '基隆市' + sight.zone}
                        </p>

                        <!-- 詳細介紹 按鈕 (點擊彈出小彈窗) -->
                        <div class="mt-auto pt-2">
                            <button class="btn btn-toggle-details btn-open-modal" data-index="${idx}">
                                <i class="fa-solid fa-arrow-up-right-from-square me-1"></i> 詳細介紹
                            </button>
                        </div>

                    </div>
                </div>
            `;
        });

        sightsContainer.innerHTML = cardsHtml;

        // 綁定詳細介紹 Modal 彈窗開關事件
        document.querySelectorAll('.btn-open-modal').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const index = parseInt(e.currentTarget.dataset.index, 10);
                openSightModal(currentSightsList[index]);
            });
        });
    }

    /**
     * 開啟景點詳細 Modal 彈窗
     */
    function openSightModal(sight) {
        if (!sight) return;

        const photoUrl = sight.photo_url || 'https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?w=800&auto=format&fit=crop';
        const googleMapsUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(sight.address || sight.sight_name)}`;

        modalSightImg.src = photoUrl;
        modalSightImg.onerror = () => {
            modalSightImg.src = 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=800&auto=format&fit=crop';
        };

        modalSightCategory.textContent = sight.category || '熱門景點';
        modalSightZone.textContent = sight.zone || '基隆市';
        modalSightTitle.textContent = sight.sight_name;
        modalSightAddress.textContent = sight.address || ('基隆市' + sight.zone);
        modalSightDesc.textContent = sight.description || '暫無詳細描述資料。';
        modalGmapsBtn.href = googleMapsUrl;

        sightDetailModal.show();
    }

    function showLoadingState() {
        sightsCountBadge.textContent = "載入中...";
        sightsContainer.innerHTML = `
            <div class="col-12 text-center py-5">
                <div class="spinner-border text-secondary" role="status" style="width: 2.2rem; height: 2.2rem;">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-3 text-muted">正在載入景點資料...</p>
            </div>
        `;
    }

    function showErrorState(msg) {
        sightsCountBadge.textContent = "載入失敗";
        sightsContainer.innerHTML = `
            <div class="col-12 text-center py-5">
                <div class="alert alert-danger d-inline-block px-4 py-3 rounded-4 shadow-sm" role="alert">
                    <i class="fa-solid fa-triangle-exclamation me-2"></i> ${msg}
                </div>
            </div>
        `;
    }
});

/**
 * 基隆景點導覽網 - JavaScript (v17.0)
 * 支援 ALL 全部景點、即時關鍵字搜尋、僅照片外框排版、Google Maps 標章
 */

document.addEventListener("DOMContentLoaded", () => {
    const districtButtonsContainer = document.getElementById("districtButtons");
    const sightsContainer = document.getElementById("sightsContainer");
    const currentDistrictTitle = document.getElementById("currentDistrictTitle");
    const sightsCountBadge = document.getElementById("sightsCountBadge");
    const searchInput = document.getElementById("searchInput");

    // Modal 元素引用
    const sightDetailModalEl = document.getElementById("sightDetailModal");
    const sightDetailModal = new bootstrap.Modal(sightDetailModalEl);

    const modalSightImg = document.getElementById("modalSightImg");
    const modalNoPhoto = document.getElementById("modalNoPhoto");
    const modalSightCategory = document.getElementById("modalSightCategory");
    const modalSightZone = document.getElementById("modalSightZone");
    const modalSightTitle = document.getElementById("modalSightTitle");
    const modalSightAddress = document.getElementById("modalSightAddress").querySelector("span");
    const modalSightDesc = document.getElementById("modalSightDesc");
    const modalGmapsBtn = document.getElementById("modalGmapsBtn");

    // 全局景點資料快取
    let currentSightsList = [];
    let filteredSightsList = [];

    // 預設載入：ALL 全部景點
    let currentZone = "ALL";
    loadSights(currentZone);

    // 行政區按鈕切換 (置於 Header 港灣背景中的 Pill 按鈕)
    if (districtButtonsContainer) {
        districtButtonsContainer.addEventListener("click", (e) => {
            const btn = e.target.closest(".btn-zone-pill");
            if (!btn) return;

            document.querySelectorAll(".btn-zone-pill").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");

            currentZone = btn.dataset.zone;
            currentDistrictTitle.textContent = currentZone === "ALL" ? "全部景點" : currentZone;
            if (searchInput) searchInput.value = "";
            loadSights(currentZone);
        });
    }

    // 關鍵字搜尋過濾
    if (searchInput) {
        searchInput.addEventListener("input", () => {
            const query = searchInput.value.trim().toLowerCase();
            if (!query) {
                filteredSightsList = [...currentSightsList];
            } else {
                filteredSightsList = currentSightsList.filter(sight => 
                    (sight.sight_name && sight.sight_name.toLowerCase().includes(query)) ||
                    (sight.address && sight.address.toLowerCase().includes(query)) ||
                    (sight.category && sight.category.toLowerCase().includes(query)) ||
                    (sight.description && sight.description.toLowerCase().includes(query))
                );
            }
            renderSights(filteredSightsList);
        });
    }

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
            filteredSightsList = [...currentSightsList];
            renderSights(filteredSightsList);
        } catch (err) {
            console.error("Fetch sights error:", err);
            showErrorState(err.message);
        }
    }

    /**
     * 渲染景點卡片 (僅照片有外框，下方景點名稱與地址無框)
     */
    function renderSights(sights) {
        if (!sights || sights.length === 0) {
            sightsContainer.innerHTML = `
                <div class="col-12 text-center py-5">
                    <i class="fa-solid fa-compass-drafting fa-3x text-muted mb-3 opacity-50"></i>
                    <p class="h5 text-muted">此區域目前無景點資料。</p>
                </div>
            `;
            sightsCountBadge.textContent = "共 0 個景點";
            return;
        }

        sightsCountBadge.textContent = `共 ${sights.length} 個景點`;

        let cardsHtml = "";
        sights.forEach((sight, idx) => {
            const googleMapsUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(sight.address || sight.sight_name)}`;
            const hasPhoto = !!(sight.photo_url && sight.photo_url.trim());

            const photoHtml = hasPhoto ? `
                <img src="${sight.photo_url}" 
                     alt="${sight.sight_name}" 
                     class="sight-photo"
                     onerror="this.style.display='none'; this.nextElementSibling.classList.remove('d-none');">
                <div class="no-photo-placeholder d-none d-flex flex-column align-items-center justify-content-center h-100 text-muted">
                    <i class="fa-regular fa-image fa-2x mb-2 opacity-50"></i>
                    <span class="no-photo-text">沒有圖片</span>
                </div>
            ` : `
                <div class="no-photo-placeholder d-flex flex-column align-items-center justify-content-center h-100 text-muted">
                    <i class="fa-regular fa-image fa-2x mb-2 opacity-50"></i>
                    <span class="no-photo-text">沒有圖片</span>
                </div>
            `;

            cardsHtml += `
                <div class="col-12 col-md-6 col-lg-4">
                    <div class="borderless-sight-card h-100 d-flex flex-column">
                        
                        <!-- ★ 點擊照片亦可開啟詳細介紹 (btn-open-modal) ★ -->
                        <div class="sight-img-container position-relative btn-open-modal" data-index="${idx}" title="點擊查看詳細介紹">
                            ${photoHtml}
                            <!-- Google Maps 浮動按鈕 (精巧尺寸、圖標與 Maps 無空隙) -->
                            <a href="${googleMapsUrl}" target="_blank" rel="noopener noreferrer" class="gmaps-floating-badge" onclick="event.stopPropagation();"><img src="/static/images/google_maps_icon.png" alt="Maps" class="gmaps-icon-img"><span>Maps</span></a>
                        </div>

                        <!-- ★ 下方景點名稱與地址：無外框，自然排列 ★ -->
                        <h3 class="borderless-sight-title btn-open-modal" data-index="${idx}" title="${sight.sight_name}">
                            ${sight.sight_name}
                        </h3>

                        <p class="borderless-sight-address mb-0 text-truncate" title="${sight.address || '基隆市' + (sight.zone || '')}">
                            <i class="fa-solid fa-map-pin me-1 text-secondary"></i>${sight.address || '基隆市' + (sight.zone || '')}
                        </p>

                    </div>
                </div>
            `;
        });

        sightsContainer.innerHTML = cardsHtml;

        // 綁定詳細介紹 Modal 彈窗開關事件
        document.querySelectorAll(".btn-open-modal").forEach(btn => {
            btn.addEventListener("click", (e) => {
                const index = parseInt(e.currentTarget.dataset.index, 10);
                openSightModal(filteredSightsList[index]);
            });
        });
    }

    /**
     * 開啟景點詳細 Modal 彈窗
     */
    function openSightModal(sight) {
        if (!sight) return;

        const googleMapsUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(sight.address || sight.sight_name)}`;
        const hasPhoto = !!(sight.photo_url && sight.photo_url.trim());

        if (hasPhoto) {
            modalSightImg.style.display = "block";
            if (modalNoPhoto) modalNoPhoto.classList.add("d-none");
            modalSightImg.src = sight.photo_url;
            modalSightImg.onerror = () => {
                modalSightImg.style.display = "none";
                if (modalNoPhoto) modalNoPhoto.classList.remove("d-none");
            };
        } else {
            modalSightImg.style.display = "none";
            if (modalNoPhoto) modalNoPhoto.classList.remove("d-none");
        }

        modalSightCategory.textContent = sight.category || "熱門景點";
        modalSightZone.textContent = sight.zone || "基隆市";
        modalSightTitle.textContent = sight.sight_name;
        modalSightAddress.textContent = sight.address || ("基隆市" + (sight.zone || ''));
        modalSightDesc.textContent = sight.description || "暫無詳細描述資料。";
        modalGmapsBtn.href = googleMapsUrl;

        sightDetailModal.show();
    }

    function showLoadingState() {
        sightsCountBadge.textContent = "載入中...";
        sightsContainer.innerHTML = `
            <div class="col-12 text-center py-5">
                <div class="spinner-border text-pink" role="status" style="width: 2.2rem; height: 2.2rem;">
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

// Variables globales
let annoncesList = [];
let filteredAnnonces = [];

// Éléments DOM
const annoncesContainer = document.getElementById('annonces-container');
const loadingElement = document.getElementById('loading');
const errorElement = document.getElementById('error');
const searchInput = document.getElementById('search');
const sortSelect = document.getElementById('sort');
const resetButton = document.getElementById('reset-filters');
const totalAnnoncesSpan = document.getElementById('total-annonces');
const dataSourceSelect = document.getElementById('data-source');
const modal = document.getElementById('modal');
const modalBody = document.getElementById('modal-body');
const closeModal = document.querySelector('.close');

// Initialisation
document.addEventListener('DOMContentLoaded', () => {
    loadAnnonces();
    setupEventListeners();
});

// Configuration des écouteurs d'événements
function setupEventListeners() {
    searchInput.addEventListener('input', filterAnnonces);
    sortSelect.addEventListener('change', sortAnnonces);
    resetButton.addEventListener('click', resetFilters);
    dataSourceSelect.addEventListener('change', loadAnnonces);
    closeModal.addEventListener('click', () => modal.style.display = 'none');
    window.addEventListener('click', (e) => {
        if (e.target === modal) modal.style.display = 'none';
    });
}

// Charger les annonces depuis le fichier JSON
async function loadAnnonces() {
    try {
        loadingElement.style.display = 'block';
        errorElement.style.display = 'none';
        annoncesContainer.innerHTML = '';

        const dataSource = dataSourceSelect.value;
        const response = await fetch(dataSource);
        
        if (!response.ok) {
            throw new Error(`Erreur HTTP: ${response.status}`);
        }

        annoncesList = await response.json();
        filteredAnnonces = [...annoncesList];
        
        loadingElement.style.display = 'none';
        updateStats();
        renderAnnonces();
    } catch (error) {
        console.error('Erreur lors du chargement des annonces:', error);
        loadingElement.style.display = 'none';
        errorElement.style.display = 'block';
    }
}

// Mettre à jour les statistiques
function updateStats() {
    totalAnnoncesSpan.textContent = `${filteredAnnonces.length} annonce${filteredAnnonces.length > 1 ? 's' : ''}`;
}

// Filtrer les annonces
function filterAnnonces() {
    const searchTerm = searchInput.value.toLowerCase().trim();
    
    if (!searchTerm) {
        filteredAnnonces = [...annoncesList];
    } else {
        filteredAnnonces = annoncesList.filter(annonce => {
            const title = (annonce.title || '').toLowerCase();
            const location = (annonce.location || '').toLowerCase();
            const price = (annonce.price || '').toLowerCase();
            const ville = (annonce.ville || '').toLowerCase();
            const quartier = (annonce.quartier || '').toLowerCase();
            
            return title.includes(searchTerm) || 
                   location.includes(searchTerm) || 
                   price.includes(searchTerm) ||
                   ville.includes(searchTerm) ||
                   quartier.includes(searchTerm);
        });
    }
    
    sortAnnonces();
}

// Trier les annonces
function sortAnnonces() {
    const sortValue = sortSelect.value;
    
    if (!sortValue) {
        renderAnnonces();
        return;
    }

    const sorted = [...filteredAnnonces].sort((a, b) => {
        if (sortValue.startsWith('price')) {
            const priceA = extractNumber(a.price) || 0;
            const priceB = extractNumber(b.price) || 0;
            return sortValue === 'price-asc' ? priceA - priceB : priceB - priceA;
        } else if (sortValue.startsWith('surface')) {
            const surfaceA = extractNumber(a.surface) || 0;
            const surfaceB = extractNumber(b.surface) || 0;
            return sortValue === 'surface-asc' ? surfaceA - surfaceB : surfaceB - surfaceA;
        }
        return 0;
    });

    filteredAnnonces = sorted;
    renderAnnonces();
}

// Extraire un nombre d'une chaîne
function extractNumber(str) {
    if (!str) return 0;
    const match = str.toString().match(/\d+/);
    return match ? parseInt(match[0]) : 0;
}

// Réinitialiser les filtres
function resetFilters() {
    searchInput.value = '';
    sortSelect.value = '';
    filteredAnnonces = [...annoncesList];
    updateStats();
    renderAnnonces();
}

// Afficher les annonces
function renderAnnonces() {
    annoncesContainer.innerHTML = '';
    updateStats();

    if (filteredAnnonces.length === 0) {
        annoncesContainer.innerHTML = '<p style="grid-column: 1/-1; text-align: center; padding: 2rem; color: var(--text-secondary);">Aucune annonce trouvée</p>';
        return;
    }

    filteredAnnonces.forEach(annonce => {
        const card = createAnnonceCard(annonce);
        annoncesContainer.appendChild(card);
    });
}

// Créer une carte d'annonce
function createAnnonceCard(annonce) {
    const card = document.createElement('div');
    card.className = 'annonce-card';
    card.onclick = () => showAnnonceDetails(annonce);

    const imageUrl = getMainImage(annonce);
    const title = truncateText(annonce.title || 'Sans titre', 100);
    const location = annonce.location || annonce.ville || 'Non spécifié';
    const price = annonce.price || 'Prix non spécifié';
    const surface = annonce.surface || 'Surface non spécifiée';
    const bedrooms = annonce.bedrooms || 'Non spécifié';

    card.innerHTML = `
        <img src="${imageUrl}" alt="${title}" class="annonce-image" onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22400%22 height=%22240%22%3E%3Crect fill=%22%23e2e8f0%22 width=%22400%22 height=%22240%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 dominant-baseline=%22middle%22 text-anchor=%22middle%22 font-family=%22sans-serif%22 font-size=%2220%22 fill=%22%2364748b%22%3EImage non disponible%3C/text%3E%3C/svg%3E'">
        <div class="annonce-content">
            <h3 class="annonce-title">${title}</h3>
            <div class="annonce-info">
                <div class="annonce-info-item">📍 ${location}</div>
                <div class="annonce-info-item">📐 ${surface}</div>
                <div class="annonce-info-item">🛏️ ${bedrooms}</div>
            </div>
            <div class="annonce-price">${price}</div>
            ${renderTags(annonce)}
        </div>
    `;

    return card;
}

// Obtenir l'image principale
function getMainImage(annonce) {
    if (annonce.images && annonce.images.length > 0) {
        // Filtrer les images de carte et autres images système
        const validImages = annonce.images.filter(img => 
            !img.includes('map') && 
            !img.includes('travel-time') &&
            !img.includes('cloudimg.io')
        );
        return validImages[0] || annonce.images[0];
    }
    return '';
}

// Afficher les tags
function renderTags(annonce) {
    if (!annonce.tags || annonce.tags.length === 0) return '';
    
    const tagsHtml = annonce.tags.slice(0, 3).map(tag => 
        `<span class="tag">${tag}</span>`
    ).join('');
    
    return `<div class="annonce-tags">${tagsHtml}</div>`;
}

// Afficher les détails d'une annonce
function showAnnonceDetails(annonce) {
    const images = renderModalImages(annonce);
    const tags = annonce.tags ? annonce.tags.map(tag => `<span class="tag">${tag}</span>`).join('') : '';
    const description = annonce.description || annonce.title || 'Pas de description disponible';
    
    modalBody.innerHTML = `
        ${images}
        
        <div class="modal-section">
            <h3>${annonce.title || 'Sans titre'}</h3>
            <div class="annonce-info">
                <div class="annonce-info-item">📍 ${annonce.location || annonce.ville || 'Non spécifié'}</div>
                <div class="annonce-info-item">📐 ${annonce.surface || 'Non spécifié'}</div>
                <div class="annonce-info-item">🛏️ ${annonce.bedrooms || 'Non spécifié'}</div>
                ${annonce.gps_latitude && annonce.gps_longitude ? 
                    `<div class="annonce-info-item">🗺️ GPS: ${annonce.gps_latitude}, ${annonce.gps_longitude}</div>` : ''}
                ${annonce.dpe ? `<div class="annonce-info-item">⚡ DPE: ${annonce.dpe}</div>` : ''}
                ${annonce.ges ? `<div class="annonce-info-item">🌍 GES: ${annonce.ges}</div>` : ''}
            </div>
            <div class="annonce-price">${annonce.price || 'Prix non spécifié'}</div>
            ${tags ? `<div class="annonce-tags" style="margin-top: 1rem;">${tags}</div>` : ''}
        </div>

        <div class="modal-section">
            <h3>Description</h3>
            <div class="modal-description">${description}</div>
        </div>

        ${annonce.url ? `<a href="${annonce.url}" target="_blank" class="modal-link">Voir l'annonce complète →</a>` : ''}
    `;

    modal.style.display = 'block';
}

// Afficher les images dans la modal
function renderModalImages(annonce) {
    if (!annonce.images || annonce.images.length === 0) return '';
    
    const validImages = annonce.images.filter(img => 
        !img.includes('map') && 
        !img.includes('travel-time') &&
        !img.includes('cloudimg.io')
    );

    if (validImages.length === 0) return '';

    const imagesHtml = validImages.slice(0, 6).map(img => 
        `<img src="${img}" alt="Photo" class="modal-image" onclick="window.open('${img}', '_blank')">`
    ).join('');

    return `<div class="modal-images">${imagesHtml}</div>`;
}

// Tronquer le texte
function truncateText(text, maxLength) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

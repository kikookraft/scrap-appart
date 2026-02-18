// Variables globales
let annoncesList = [];
let filteredAnnonces = [];
const DATA_URL = '/api/annonces'; // URL du proxy serveur
const LOCAL_CACHE = 'annonces_cache.json'; // Fichier de cache local

// Carte
let map = null;
let markersLayer = null;
let currentView = 'list'; // 'list' ou 'map'

// Debounce timer pour optimiser les filtres
let filterDebounceTimer = null;
const DEBOUNCE_DELAY = 300; // millisecondes

// Éléments DOM
const annoncesContainer = document.getElementById('annonces-container');
const loadingElement = document.getElementById('loading');
const errorElement = document.getElementById('error');
const searchInput = document.getElementById('search');
const sortSelect = document.getElementById('sort');
const resetButton = document.getElementById('reset-filters');
const totalAnnoncesSpan = document.getElementById('total-annonces');
const modal = document.getElementById('modal');
const modalBody = document.getElementById('modal-body');
const closeModal = document.querySelector('.close');

// Nouveaux éléments pour les filtres avancés
const toggleAdvancedBtn = document.getElementById('toggle-advanced');
const advancedFilters = document.getElementById('advanced-filters');
const priceMinInput = document.getElementById('price-min');
const priceMaxInput = document.getElementById('price-max');
const surfaceMinInput = document.getElementById('surface-min');
const surfaceMaxInput = document.getElementById('surface-max');
const bedroomsFilter = document.getElementById('bedrooms-filter');
const roomsFilter = document.getElementById('rooms-filter');
const cityFilter = document.getElementById('city-filter');

// Initialisation
document.addEventListener('DOMContentLoaded', () => {
    loadAnnonces();
    setupEventListeners();
    initMap();
});

// Configuration des écouteurs d'événements
function setupEventListeners() {
    // Recherche instantanée avec debounce
    searchInput.addEventListener('input', debouncedFilter);
    
    // Select sans debounce (changement unique)
    sortSelect.addEventListener('change', sortAnnonces);
    bedroomsFilter.addEventListener('change', filterAnnonces);
    roomsFilter.addEventListener('change', filterAnnonces);
    cityFilter.addEventListener('change', filterAnnonces);
    
    resetButton.addEventListener('click', resetFilters);
    closeModal.addEventListener('click', () => modal.style.display = 'none');
    window.addEventListener('click', (e) => {
        if (e.target === modal) modal.style.display = 'none';
    });
    
    // Nouveaux écouteurs pour les filtres avancés avec debounce
    toggleAdvancedBtn.addEventListener('click', toggleAdvancedFilters);
    priceMinInput.addEventListener('input', debouncedFilter);
    priceMaxInput.addEventListener('input', debouncedFilter);
    surfaceMinInput.addEventListener('input', debouncedFilter);
    surfaceMaxInput.addEventListener('input', debouncedFilter);
    
    // Onglets
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });
}

// Fonction debounce pour optimiser les filtres
function debouncedFilter() {
    // Annuler le timer précédent
    if (filterDebounceTimer) {
        clearTimeout(filterDebounceTimer);
    }
    
    // Afficher un indicateur visuel subtil (optionnel)
    totalAnnoncesSpan.style.opacity = '0.5';
    
    // Créer un nouveau timer
    filterDebounceTimer = setTimeout(() => {
        filterAnnonces();
        totalAnnoncesSpan.style.opacity = '1';
    }, DEBOUNCE_DELAY);
}

// Toggle des filtres avancés
function toggleAdvancedFilters() {
    const isVisible = advancedFilters.style.display !== 'none';
    advancedFilters.style.display = isVisible ? 'none' : 'grid';
    toggleAdvancedBtn.textContent = isVisible ? '🔽 Filtres avancés' : '🔼 Masquer les filtres';
}

// Charger les annonces depuis l'URL ou le cache
async function loadAnnonces() {
    try {
        loadingElement.style.display = 'block';
        errorElement.style.display = 'none';
        annoncesContainer.innerHTML = '';

        // Essayer de charger depuis l'URL
        let response = await fetch(DATA_URL);
        
        if (!response.ok) {
            // Si l'URL échoue, essayer le cache local
            console.log('Tentative de chargement depuis le cache local...');
            response = await fetch(LOCAL_CACHE);
        }
        
        if (!response.ok) {
            throw new Error(`Erreur HTTP: ${response.status}`);
        }

        const data = await response.json();
        annoncesList = Array.isArray(data) ? data : [data];
        filteredAnnonces = [...annoncesList];
        
        loadingElement.style.display = 'none';
        populateCityFilter(); // Remplir le filtre des villes
        updateStats();
        renderAnnonces();
    } catch (error) {
        console.error('Erreur lors du chargement des annonces:', error);
        loadingElement.style.display = 'none';
        errorElement.style.display = 'block';
        errorElement.innerHTML = `
            <p>❌ Erreur lors du chargement des annonces</p>
            <p style="font-size: 0.9rem; margin-top: 0.5rem;">${error.message}</p>
        `;
    }
}

// Mettre à jour les statistiques
function updateStats() {
    totalAnnoncesSpan.textContent = `${filteredAnnonces.length} annonce${filteredAnnonces.length > 1 ? 's' : ''}`;
}

// Remplir le filtre des villes
function populateCityFilter() {
    const cities = new Set();
    annoncesList.forEach(annonce => {
        const city = annonce.location?.address?.city;
        if (city) cities.add(city);
    });
    
    // Trier les villes par ordre alphabétique
    const sortedCities = Array.from(cities).sort();
    
    // Vider et remplir le select
    cityFilter.innerHTML = '<option value="">Toutes les villes</option>';
    sortedCities.forEach(city => {
        const option = document.createElement('option');
        option.value = city;
        option.textContent = city;
        cityFilter.appendChild(option);
    });
}

// Filtrer les annonces
function filterAnnonces() {
    const searchTerm = searchInput.value.toLowerCase().trim();
    const priceMin = parseFloat(priceMinInput.value) || 0;
    const priceMax = parseFloat(priceMaxInput.value) || Infinity;
    const surfaceMin = parseFloat(surfaceMinInput.value) || 0;
    const surfaceMax = parseFloat(surfaceMaxInput.value) || Infinity;
    const minBedrooms = parseInt(bedroomsFilter.value) || 0;
    const minRooms = parseInt(roomsFilter.value) || 0;
    const selectedCity = cityFilter.value;
    
    filteredAnnonces = annoncesList.filter(annonce => {
        // Filtre de recherche textuelle
        if (searchTerm) {
            const title = (annonce.hardFacts?.title || annonce.mainDescription?.headline || '').toLowerCase();
            const city = (annonce.location?.address?.city || '').toLowerCase();
            const district = (annonce.location?.address?.district || '').toLowerCase();
            const zipCode = (annonce.location?.address?.zipCode || '').toLowerCase();
            const price = (annonce.hardFacts?.price?.formatted || '').toLowerCase();
            const description = (annonce.mainDescription?.description || '').toLowerCase();
            
            const matchesSearch = title.includes(searchTerm) || 
                                city.includes(searchTerm) || 
                                district.includes(searchTerm) ||
                                zipCode.includes(searchTerm) ||
                                price.includes(searchTerm) ||
                                description.includes(searchTerm);
            
            if (!matchesSearch) return false;
        }
        
        // Filtre de prix
        const price = extractPrice(annonce.hardFacts?.price?.value || annonce.rawData?.price);
        if (price < priceMin || price > priceMax) return false;
        
        // Filtre de surface
        const surface = extractSurface(annonce);
        if (surface < surfaceMin || surface > surfaceMax) return false;
        
        // Filtre de chambres
        const bedrooms = extractBedrooms(annonce);
        if (bedrooms < minBedrooms) return false;
        
        // Filtre de pièces
        const rooms = extractRooms(annonce);
        if (rooms < minRooms) return false;
        
        // Filtre de ville
        if (selectedCity) {
            const annonceCity = annonce.location?.address?.city || '';
            if (annonceCity !== selectedCity) return false;
        }
        
        return true;
    });
    
    sortAnnonces();
}

// Extraire le nombre de chambres
function extractBedrooms(annonce) {
    if (annonce.rawData?.nbbedroom) {
        return parseInt(annonce.rawData.nbbedroom);
    }
    if (annonce.hardFacts?.facts) {
        const bedroomsFact = annonce.hardFacts.facts.find(f => f.type === 'numberOfBedrooms');
        if (bedroomsFact?.splitValue) {
            return parseInt(bedroomsFact.splitValue);
        }
    }
    return 0;
}

// Extraire le nombre de pièces
function extractRooms(annonce) {
    if (annonce.rawData?.nbroom) {
        return parseInt(annonce.rawData.nbroom);
    }
    if (annonce.hardFacts?.facts) {
        const roomsFact = annonce.hardFacts.facts.find(f => f.type === 'numberOfRooms');
        if (roomsFact?.splitValue) {
            return parseInt(roomsFact.splitValue);
        }
    }
    return 0;
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
            const priceA = extractPrice(a.hardFacts?.price?.value || a.rawData?.price) || 0;
            const priceB = extractPrice(b.hardFacts?.price?.value || b.rawData?.price) || 0;
            return sortValue === 'price-asc' ? priceA - priceB : priceB - priceA;
        } else if (sortValue.startsWith('surface')) {
            const surfaceA = extractSurface(a) || 0;
            const surfaceB = extractSurface(b) || 0;
            return sortValue === 'surface-asc' ? surfaceA - surfaceB : surfaceB - surfaceA;
        }
        return 0;
    });

    filteredAnnonces = sorted;
    renderAnnonces();
}

// Extraire le prix d'une annonce
function extractPrice(price) {
    if (typeof price === 'number') return price;
    if (!price) return 0;
    const match = price.toString().replace(/\s/g, '').match(/\d+/);
    return match ? parseInt(match[0]) : 0;
}

// Extraire la surface d'une annonce
function extractSurface(annonce) {
    // Chercher dans rawData.surface.main
    if (annonce.rawData?.surface?.main) {
        return parseFloat(annonce.rawData.surface.main);
    }
    
    // Chercher dans hardFacts.facts
    if (annonce.hardFacts?.facts) {
        const surfaceFact = annonce.hardFacts.facts.find(f => f.type === 'livingSpace');
        if (surfaceFact?.splitValue) {
            return parseFloat(surfaceFact.splitValue.replace(',', '.'));
        }
    }
    
    return 0;
}

// Réinitialiser les filtres
function resetFilters() {
    searchInput.value = '';
    sortSelect.value = '';
    priceMinInput.value = '';
    priceMaxInput.value = '';
    surfaceMinInput.value = '';
    surfaceMaxInput.value = '';
    bedroomsFilter.value = '';
    roomsFilter.value = '';
    cityFilter.value = '';
    filteredAnnonces = [...annoncesList];
    updateStats();
    renderAnnonces();
}

// Afficher les annonces
function renderAnnonces() {
    updateStats();

    if (filteredAnnonces.length === 0) {
        annoncesContainer.innerHTML = '<p style="grid-column: 1/-1; text-align: center; padding: 2rem; color: var(--text-secondary);">Aucune annonce trouvée</p>';
        // Mettre à jour la carte aussi
        if (currentView === 'map' && map) {
            updateMapMarkers();
        }
        return;
    }

    // Utiliser un fragment pour améliorer les performances
    const fragment = document.createDocumentFragment();
    
    filteredAnnonces.forEach(annonce => {
        const card = createAnnonceCard(annonce);
        fragment.appendChild(card);
    });
    
    // Mettre à jour le DOM en une seule fois
    annoncesContainer.innerHTML = '';
    annoncesContainer.appendChild(fragment);
    
    // Mettre à jour la carte si on est en vue carte
    if (currentView === 'map' && map) {
        updateMapMarkers();
    }
}

// Créer une carte d'annonce
function createAnnonceCard(annonce) {
    const card = document.createElement('div');
    card.className = 'annonce-card';
    card.onclick = () => showAnnonceDetails(annonce);

    const imageUrl = getMainImage(annonce);
    const title = truncateText(
        annonce.hardFacts?.title || annonce.mainDescription?.headline || 'Sans titre', 
        100
    );
    const city = annonce.location?.address?.city || 'Non spécifié';
    const district = annonce.location?.address?.district || '';
    const location = district ? `${city} - ${district}` : city;
    const price = annonce.hardFacts?.price?.formatted || 'Prix non spécifié';
    
    // Extraire les informations depuis hardFacts.facts
    let surface = 'N/A';
    let rooms = 'N/A';
    let bedrooms = 'N/A';
    let floor = '';
    
    if (annonce.hardFacts?.facts) {
        const surfaceFact = annonce.hardFacts.facts.find(f => f.type === 'livingSpace');
        const roomsFact = annonce.hardFacts.facts.find(f => f.type === 'numberOfRooms');
        const bedroomsFact = annonce.hardFacts.facts.find(f => f.type === 'numberOfBedrooms');
        const floorFact = annonce.hardFacts.facts.find(f => f.type === 'numberOfFloors');
        
        if (surfaceFact) surface = surfaceFact.value;
        if (roomsFact) rooms = roomsFact.value;
        if (bedroomsFact) bedrooms = bedroomsFact.value;
        if (floorFact) floor = floorFact.value;
    }

    // Déterminer les tags
    const tags = [];
    if (annonce.tags?.isNew) tags.push('Nouveau');
    if (annonce.tags?.isExclusive) tags.push('Exclusif');
    if (annonce.tags?.has3DVisit) tags.push('Visite 3D');
    if (annonce.tags?.hasBrokerageFee === false) tags.push('Sans frais');

    card.innerHTML = `
        <img src="${imageUrl}" alt="${title}" class="annonce-image" onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22400%22 height=%22240%22%3E%3Crect fill=%22%23e2e8f0%22 width=%22400%22 height=%22240%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 dominant-baseline=%22middle%22 text-anchor=%22middle%22 font-family=%22sans-serif%22 font-size=%2220%22 fill=%22%2364748b%22%3EImage non disponible%3C/text%3E%3C/svg%3E'">
        <div class="annonce-content">
            <h3 class="annonce-title">${title}</h3>
            <div class="annonce-info">
                <div class="annonce-info-item">📍 ${location}</div>
                <div class="annonce-info-item">📐 ${surface}</div>
                <div class="annonce-info-item">🏠 ${rooms}</div>
                <div class="annonce-info-item">🛏️ ${bedrooms}</div>
            </div>
            ${floor ? `<div class="annonce-info-item" style="margin-top: 0.5rem;">📶 ${floor}</div>` : ''}
            <div class="annonce-price">${price}</div>
            ${renderTags(tags)}
        </div>
    `;

    return card;
}

// Obtenir l'image principale
function getMainImage(annonce) {
    if (annonce.gallery?.images && annonce.gallery.images.length > 0) {
        // Prendre la première image de la galerie
        return annonce.gallery.images[0].url;
    }
    return '';
}

// Afficher les tags
function renderTags(tags) {
    if (!tags || tags.length === 0) return '';
    
    const tagsHtml = tags.slice(0, 4).map(tag => 
        `<span class="tag">${tag}</span>`
    ).join('');
    
    return `<div class="annonce-tags">${tagsHtml}</div>`;
}

// Afficher les détails d'une annonce
function showAnnonceDetails(annonce) {
    const images = renderModalImages(annonce);
    const title = annonce.hardFacts?.title || annonce.mainDescription?.headline || 'Sans titre';
    const city = annonce.location?.address?.city || 'Non spécifié';
    const district = annonce.location?.address?.district || '';
    const zipCode = annonce.location?.address?.zipCode || '';
    const location = district ? `${city} - ${district} (${zipCode})` : `${city} (${zipCode})`;
    const price = annonce.hardFacts?.price?.formatted || 'Prix non spécifié';
    const priceInfo = annonce.hardFacts?.price?.additionalInformation || '';
    
    // Extraire les informations depuis hardFacts
    let infoItems = '';
    if (annonce.hardFacts?.facts) {
        infoItems = annonce.hardFacts.facts.map(fact => {
            const icons = {
                'numberOfRooms': '🏠',
                'numberOfBedrooms': '🛏️',
                'livingSpace': '📐',
                'numberOfFloors': '📶',
                'plotSize': '🌳',
                'numberOfBathrooms': '🚿'
            };
            const icon = icons[fact.type] || '•';
            return `<div class="annonce-info-item">${icon} ${fact.value}</div>`;
        }).join('');
    }
    
    // Tags
    const tags = [];
    if (annonce.tags?.isNew) tags.push('Nouveau');
    if (annonce.tags?.isExclusive) tags.push('Exclusif');
    if (annonce.tags?.has3DVisit) tags.push('Visite 3D');
    if (annonce.tags?.hasBrokerageFee === false) tags.push('Sans frais');
    const tagsHtml = tags.length > 0 ? tags.map(tag => `<span class="tag">${tag}</span>`).join('') : '';
    
    // Description
    const description = annonce.mainDescription?.description || annonce.mainDescription?.headline || 'Pas de description disponible';
    
    // Informations du fournisseur
    let providerInfo = '';
    if (annonce.provider) {
        const providerName = annonce.provider.intermediaryCard?.title || annonce.provider.contactCard?.title || '';
        const providerType = annonce.provider.intermediaryCard?.subtitle || '';
        const phone = annonce.provider.phoneNumbers?.join(', ') || '';
        const address = annonce.provider.address || '';
        
        providerInfo = `
            <div class="modal-section">
                <h3>Contact</h3>
                <div style="margin-top: 0.5rem;">
                    ${providerName ? `<div><strong>${providerName}</strong></div>` : ''}
                    ${providerType ? `<div style="color: var(--text-secondary); font-size: 0.9rem;">${providerType}</div>` : ''}
                    ${phone ? `<div style="margin-top: 0.5rem;">📞 ${phone}</div>` : ''}
                    ${address ? `<div style="margin-top: 0.25rem; font-size: 0.9rem; color: var(--text-secondary);">📍 ${address}</div>` : ''}
                </div>
            </div>
        `;
    }
    
    modalBody.innerHTML = `
        ${images}
        
        <div class="modal-section">
            <h3>${title}</h3>
            <div class="annonce-info">
                <div class="annonce-info-item">📍 ${location}</div>
                ${infoItems}
            </div>
            <div class="annonce-price">${price}${priceInfo ? ` <span style="font-size: 0.8rem; font-weight: normal;">(${priceInfo})</span>` : ''}</div>
            ${tagsHtml ? `<div class="annonce-tags" style="margin-top: 1rem;">${tagsHtml}</div>` : ''}
        </div>

        <div class="modal-section">
            <h3>Description</h3>
            <div class="modal-description">${description}</div>
        </div>

        ${providerInfo}

        ${annonce.url ? `<a href="${annonce.url}" target="_blank" class="modal-link">Voir l'annonce complète →</a>` : ''}
    `;

    modal.style.display = 'block';
}

// Afficher les images dans la modal
function renderModalImages(annonce) {
    if (!annonce.gallery?.images || annonce.gallery.images.length === 0) return '';

    const imagesHtml = annonce.gallery.images.slice(0, 8).map(img => 
        `<img src="${img.url}" alt="${img.alt || 'Photo'}" class="modal-image" onclick="window.open('${img.url}', '_blank')">`
    ).join('');

    return `<div class="modal-images">${imagesHtml}</div>`;
}

// Tronquer le texte
function truncateText(text, maxLength) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

// ==================== GESTION DE LA CARTE ====================

// Initialiser la carte
function initMap() {
    // Créer la carte centrée sur Lyon par défaut
    map = L.map('map').setView([45.75, 4.85], 12);
    
    // Ajouter les tuiles OpenStreetMap
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(map);
    
    // Créer un groupe de marqueurs avec clustering
    markersLayer = L.markerClusterGroup({
        maxClusterRadius: 50, // Rayon de clustering en pixels
        spiderfyOnMaxZoom: true,
        showCoverageOnHover: false,
        zoomToBoundsOnClick: true,
        iconCreateFunction: function(cluster) {
            const count = cluster.getChildCount();
            let size = 'small';
            if (count > 100) size = 'large';
            else if (count > 10) size = 'medium';
            
            return L.divIcon({
                html: `<div class="cluster-icon cluster-${size}">${count}</div>`,
                className: 'custom-cluster-icon',
                iconSize: L.point(40, 40)
            });
        }
    }).addTo(map);
}

// Switch entre les onglets
function switchTab(tabName) {
    console.log('Switching to tab:', tabName);
    currentView = tabName;
    
    // Mettre à jour les boutons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
    });
    
    // Mettre à jour le contenu
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabName}-view`).classList.add('active');
    
    // Si on passe à la carte, la mettre à jour
    if (tabName === 'map') {
        console.log('Switching to map view, updating markers...');
        setTimeout(() => {
            if (map) {
                map.invalidateSize(); // Rafraîchir la taille de la carte
                updateMapMarkers();
            } else {
                console.error('Map not initialized!');
            }
        }, 100);
    }
}

// Mettre à jour les marqueurs sur la carte
function updateMapMarkers() {
    console.log('Updating map markers...', filteredAnnonces.length, 'annonces');
    
    // Vider les marqueurs existants
    markersLayer.clearLayers();
    
    // Filtrer les annonces avec coordonnées GPS
    const annoncesWithCoords = filteredAnnonces.filter(annonce => {
        return annonce.rawData?.geoIdHierarchy || 
               (annonce.location?.coordinates?.latitude && annonce.location?.coordinates?.longitude) ||
               annonce.location?.address?.city; // Ajouter cette condition pour utiliser la géolocalisation par ville
    });
    
    console.log('Annonces with coordinates:', annoncesWithCoords.length);
    
    if (annoncesWithCoords.length === 0) {
        console.log('Aucune annonce avec coordonnées GPS');
        return;
    }
    
    // Préparer les coordonnées pour centrer la carte
    const bounds = [];
    
    annoncesWithCoords.forEach(annonce => {
        const coords = getAnnonceCoordinates(annonce);
        if (!coords) return;
        
        bounds.push([coords.lat, coords.lng]);
        
        // Créer un marqueur personnalisé avec le prix
        const price = annonce.hardFacts?.price?.value || 
                     (annonce.rawData?.price ? `${annonce.rawData.price} €` : 'N/A');
        
        const icon = L.divIcon({
            className: 'custom-marker',
            html: `<div class="price-marker">${price}</div>`,
            iconSize: [80, 40],
            iconAnchor: [40, 40]
        });
        
        const marker = L.marker([coords.lat, coords.lng], { icon })
            .addTo(markersLayer);
        
        // Créer le popup
        const popupContent = createMapPopup(annonce);
        marker.bindPopup(popupContent, {
            maxWidth: 300,
            className: 'custom-popup'
        });
        
        // Gérer le clic sur le marqueur
        marker.on('click', () => {
            // Mettre en surbrillance le marqueur
            document.querySelectorAll('.price-marker').forEach(m => {
                m.classList.remove('selected');
            });
            marker.getElement().querySelector('.price-marker').classList.add('selected');
        });
    });
    
    // Ajuster la vue pour montrer tous les marqueurs
    if (bounds.length > 0) {
        map.fitBounds(bounds, { padding: [50, 50] });
    }
}

// Obtenir les coordonnées d'une annonce
function getAnnonceCoordinates(annonce) {
    // Coordonnées directes
    if (annonce.location?.coordinates?.latitude && annonce.location?.coordinates?.longitude) {
        return {
            lat: annonce.location.coordinates.latitude,
            lng: annonce.location.coordinates.longitude
        };
    }
    
    // Extraire les informations de localisation
    const city = annonce.location?.address?.city?.toLowerCase() || '';
    const district = annonce.location?.address?.district?.toLowerCase() || '';
    const zipCode = annonce.location?.address?.zipCode || '';
    
    // Base de données détaillée des quartiers de Lyon
    const lyonDistricts = {
        // Lyon 1er
        'pentes': [45.770, 4.831],
        'terreaux': [45.767, 4.834],
        'hôtel de ville': [45.767, 4.836],
        'martinière': [45.773, 4.829],
        
        // Lyon 2ème
        'ainay': [45.750, 4.826],
        'bellecour': [45.757, 4.833],
        'perrache': [45.746, 4.825],
        'confluence': [45.740, 4.815],
        'carnot': [45.751, 4.827],
        
        // Lyon 3ème
        'part-dieu': [45.760, 4.856],
        'part dieu': [45.760, 4.856],
        'préfecture': [45.754, 4.845],
        'liberté': [45.754, 4.845],
        'préfecture liberté': [45.754, 4.845],
        'villette': [45.762, 4.870],
        'montchat': [45.755, 4.880],
        'grange blanche': [45.745, 4.875],
        'sans souci': [45.747, 4.867],
        'dauphiné': [45.760, 4.863],
        
        // Lyon 4ème
        'croix-rousse': [45.778, 4.827],
        'plateau': [45.778, 4.827],
        'serin': [45.786, 4.827],
        
        // Lyon 5ème
        'vieux-lyon': [45.763, 4.826],
        'vieux lyon': [45.763, 4.826],
        'fourvière': [45.762, 4.823],
        'saint-just': [45.757, 4.815],
        'point du jour': [45.749, 4.799],
        'ménival': [45.749, 4.799],
        'point du jour-ménival': [45.749, 4.799],
        
        // Lyon 6ème
        'brotteaux': [45.770, 4.850],
        'bellecombe': [45.769, 4.865],
        'tête d\'or': [45.778, 4.852],
        'foch': [45.770, 4.843],
        'masséna': [45.771, 4.846],
        'vitton': [45.774, 4.856],
        
        // Lyon 7ème
        'jean macé': [45.745, 4.841],
        'gerland': [45.726, 4.837],
        'guillotière': [45.750, 4.842],
        'garibaldi': [45.753, 4.851],
        'jean jaurès': [45.747, 4.846],
        
        // Lyon 8ème
        'monplaisir': [45.738, 4.877],
        'états-unis': [45.740, 4.867],
        'etats-unis': [45.740, 4.867],
        'mermoz': [45.732, 4.876],
        'moulin à vent': [45.744, 4.865],
        'transvaal': [45.737, 4.871],
        'bachut': [45.729, 4.863],
        
        // Lyon 9ème
        'vaise': [45.781, 4.805],
        'gorge de loup': [45.766, 4.804],
        'duchère': [45.788, 4.798],
        'saint-rambert': [45.810, 4.833],
        'rochecardon': [45.781, 4.805],
        'industrie': [45.781, 4.805],
        'vaise-rochecardon-industrie': [45.781, 4.805]
    };
    
    // Base de données des villes
    const cityCoords = {
        'lyon': [45.75, 4.85],
        'lyon 1er': [45.767, 4.834],
        'lyon 2ème': [45.746, 4.825],
        'lyon 3ème': [45.754, 4.856],
        'lyon 4ème': [45.778, 4.827],
        'lyon 5ème': [45.757, 4.804],
        'lyon 6ème': [45.770, 4.850],
        'lyon 7ème': [45.735, 4.840],
        'lyon 8ème': [45.737, 4.871],
        'lyon 9ème': [45.780, 4.805],
        'villeurbanne': [45.766, 4.880],
        'paris': [48.856, 2.352],
        'marseille': [43.296, 5.370],
        'lille': [50.629, 3.057],
        'toulouse': [43.604, 1.444],
        'nice': [43.710, 7.262],
        'nantes': [47.218, -1.554],
        'strasbourg': [48.573, 7.752],
        'montpellier': [43.611, 3.877],
        'bordeaux': [44.837, -0.579],
        'rennes': [48.117, -1.677]
    };
    
    // Chercher d'abord par quartier (plus précis)
    if (district) {
        for (const [districtName, coords] of Object.entries(lyonDistricts)) {
            if (district.includes(districtName) || districtName.includes(district)) {
                // Ajouter une petite variation aléatoire pour disperser les marqueurs (~200m)
                const lat = coords[0] + (Math.random() - 0.5) * 0.003;
                const lng = coords[1] + (Math.random() - 0.5) * 0.003;
                return { lat, lng };
            }
        }
    }
    
    // Sinon chercher par ville/arrondissement
    if (city) {
        for (const [cityName, coords] of Object.entries(cityCoords)) {
            if (city.includes(cityName)) {
                // Variation plus importante si pas de quartier spécifique (~500m)
                const lat = coords[0] + (Math.random() - 0.5) * 0.008;
                const lng = coords[1] + (Math.random() - 0.5) * 0.008;
                return { lat, lng };
            }
        }
    }
    
    return null;
}

// Créer le contenu du popup
function createMapPopup(annonce) {
    const imageUrl = getMainImage(annonce);
    const title = truncateText(
        annonce.hardFacts?.title || annonce.mainDescription?.headline || 'Sans titre', 
        60
    );
    const city = annonce.location?.address?.city || '';
    const district = annonce.location?.address?.district || '';
    const location = district ? `${city} - ${district}` : city;
    const price = annonce.hardFacts?.price?.formatted || 'Prix non spécifié';
    
    // Extraire les infos
    let surface = 'N/A';
    let rooms = 'N/A';
    let bedrooms = 'N/A';
    
    if (annonce.hardFacts?.facts) {
        const surfaceFact = annonce.hardFacts.facts.find(f => f.type === 'livingSpace');
        const roomsFact = annonce.hardFacts.facts.find(f => f.type === 'numberOfRooms');
        const bedroomsFact = annonce.hardFacts.facts.find(f => f.type === 'numberOfBedrooms');
        
        if (surfaceFact) surface = surfaceFact.value;
        if (roomsFact) rooms = roomsFact.value;
        if (bedroomsFact) bedrooms = bedroomsFact.value;
    }
    
    return `
        <div class="map-popup-card">
            ${imageUrl ? `<img src="${imageUrl}" alt="${title}" class="map-popup-image" onerror="this.style.display='none'">` : ''}
            <div class="map-popup-content">
                <div class="map-popup-title">${title}</div>
                <div class="map-popup-location">📍 ${location}</div>
                <div class="map-popup-info">
                    <span>📐 ${surface}</span>
                    <span>🏠 ${rooms}</span>
                    <span>🛏️ ${bedrooms}</span>
                </div>
                <div class="map-popup-price">${price}</div>
                <button class="map-popup-btn" onclick="showAnnonceDetailsFromMap('${annonce.id}')">
                    Voir les détails
                </button>
            </div>
        </div>
    `;
}

// Afficher les détails d'une annonce depuis la carte
function showAnnonceDetailsFromMap(annonceId) {
    const annonce = annoncesList.find(a => a.id === annonceId);
    if (annonce) {
        showAnnonceDetails(annonce);
    }
}

// Exposer les fonctions nécessaires au scope global pour les onclick
window.showAnnonceDetailsFromMap = showAnnonceDetailsFromMap;

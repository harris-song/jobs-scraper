document.addEventListener('DOMContentLoaded', function() {
    // Global variables
    let allJobs = [];
    let filteredJobs = [];
    let uniqueLocations = new Set();
    let currentPage = 1;
    const jobsPerPage = 9;
    let selectedCompany = 'all';
    let selectedLocation = 'all';
    
    // Get DOM elements
    const jobsContainer = document.getElementById('jobs-container');
    const searchInput = document.getElementById('search-input');
    const companyDropdownBtn = document.getElementById('company-dropdown-btn');
    const locationDropdownBtn = document.getElementById('location-dropdown-btn');
    const companyDropdown = document.getElementById('company-dropdown');
    const locationDropdown = document.getElementById('location-dropdown');
    const totalCountEl = document.querySelector('#total-count .stat-card-value');
    const companiesCountEl = document.querySelector('#companies-count .stat-card-value');
    const locationsCountEl = document.querySelector('#locations-count .stat-card-value');
    const lastUpdatedEl = document.querySelector('#last-updated .stat-card-date');
    const footerLastUpdatedEl = document.getElementById('footer-last-updated');
    const prevPageBtn = document.getElementById('prev-page');
    const nextPageBtn = document.getElementById('next-page');
    const pageInfoEl = document.getElementById('page-info');
    const loadingSpinner = document.getElementById('loading-spinner');
    const themeToggle = document.getElementById('theme-toggle');
    
    // Initialize theme from localStorage or system preference
    initTheme();
    
    // Job card template
    const jobCardTemplate = document.getElementById('job-card-template');
    
    // Company logo URLs
    const companyLogos = {
        accenture: 'https://upload.wikimedia.org/wikipedia/commons/c/cd/Accenture.svg',
        apple: 'https://upload.wikimedia.org/wikipedia/commons/f/fa/Apple_logo_black.svg',
        meta: 'https://upload.wikimedia.org/wikipedia/commons/7/7b/Meta_Platforms_Inc._logo.svg',
        nvidia: 'https://upload.wikimedia.org/wikipedia/en/2/2f/Nvidia_logo.svg',
        salesforce: 'https://upload.wikimedia.org/wikipedia/en/f/f9/Salesforce.com_logo.svg',
        tesla: 'https://upload.wikimedia.org/wikipedia/commons/e/e8/Tesla_logo.png'
    };
    
    // Function to initialize theme
    function initTheme() {
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'dark' || (!savedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
            document.body.classList.add('dark-theme');
        }
    }
    
    // Initialize the app
    initApp();
    
    async function initApp() {
        try {
            // Load all company job data
            const companies = ['accenture', 'apple', 'meta', 'nvidia', 'salesforce', 'tesla'];
            const promises = companies.map(company => 
                fetch(`jobs/${company}_jobs_processed.json`)
                    .then(response => {
                        if (!response.ok) {
                            throw new Error(`Failed to load ${company} jobs: ${response.status}`);
                        }
                        return response.json();
                    })
                    .then(data => {
                        // Add company name to each job
                        return data.map(job => ({...job, company}));
                    })
                    .catch(error => {
                        console.error(error);
                        return []; // Return empty array if fetch fails
                    })
            );
            
            // Wait for all data to be fetched
            const results = await Promise.all(promises);
            
            // Combine all jobs into one array
            allJobs = results.flat();
            
            // Get unique locations for the filter
            allJobs.forEach(job => {
                if (job.Location && typeof job.Location === 'string') {
                    // Clean up and normalize location
                    const cleanLocation = job.Location.trim();
                    if (cleanLocation) {
                        uniqueLocations.add(cleanLocation);
                    }
                }
            });
            
            // Populate location filter
            populateLocationFilter();
            
            // Update stats
            updateStats();
            
            // Set the initial filtered jobs
            filteredJobs = [...allJobs];
            
            // Render the jobs
            renderJobs();
            
            // Hide loading spinner
            loadingSpinner.style.display = 'none';
            
            // Add event listeners
            setupEventListeners();
            
        } catch (error) {
            console.error('Error initializing app:', error);
            jobsContainer.innerHTML = `<div class="error-message">
                <h3>Failed to load job data</h3>
                <p>${error.message}</p>
            </div>`;
            loadingSpinner.style.display = 'none';
        }
    }
    
    function populateLocationFilter() {
        // Sort locations alphabetically
        const sortedLocations = Array.from(uniqueLocations).sort();
        
        // Add options to location dropdown
        sortedLocations.forEach(location => {
            const item = document.createElement('div');
            item.className = 'dropdown-item';
            item.dataset.value = location;
            item.textContent = location;
            item.addEventListener('click', () => selectLocation(location));
            locationDropdown.appendChild(item);
        });
    }
    
    function updateStats() {
        // Update total jobs count
        totalCountEl.textContent = allJobs.length.toLocaleString();
        
        // Update companies count (unique companies)
        const uniqueCompanies = new Set(allJobs.map(job => job.company));
        companiesCountEl.textContent = uniqueCompanies.size;
        
        // Update locations count
        locationsCountEl.textContent = uniqueLocations.size;
        
        // Update last updated date
        const today = new Date();
        const formattedDate = today.toLocaleString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        lastUpdatedEl.textContent = formattedDate;
        footerLastUpdatedEl.textContent = formattedDate;
    }
    
    function setupEventListeners() {
        // Search input event
        searchInput.addEventListener('input', handleSearch);
        
        // Theme toggle
        themeToggle.addEventListener('click', toggleTheme);
        
        // Dropdown toggles
        companyDropdownBtn.addEventListener('click', () => toggleDropdown('company'));
        locationDropdownBtn.addEventListener('click', () => toggleDropdown('location'));
        
        // Close dropdowns when clicking outside
        document.addEventListener('click', (event) => {
            if (!event.target.closest('.dropdown')) {
                document.querySelectorAll('.dropdown').forEach(dropdown => {
                    dropdown.classList.remove('active');
                });
            }
        });
        
        // Company dropdown items
        document.querySelectorAll('#company-dropdown .dropdown-item').forEach(item => {
            item.addEventListener('click', () => selectCompany(item.dataset.value));
        });
        
        // Pagination events
        prevPageBtn.addEventListener('click', () => {
            if (currentPage > 1) {
                currentPage--;
                renderJobs();
                window.scrollTo({top: 0, behavior: 'smooth'});
            }
        });
        
        nextPageBtn.addEventListener('click', () => {
            const maxPages = Math.ceil(filteredJobs.length / jobsPerPage);
            if (currentPage < maxPages) {
                currentPage++;
                renderJobs();
                window.scrollTo({top: 0, behavior: 'smooth'});
            }
        });
    }
    
    function toggleDropdown(type) {
        const dropdown = document.getElementById(`${type}-dropdown`).parentElement;
        
        // Close all other dropdowns
        document.querySelectorAll('.dropdown').forEach(el => {
            if (el !== dropdown) el.classList.remove('active');
        });
        
        // Toggle this dropdown
        dropdown.classList.toggle('active');
    }
    
    function selectCompany(company) {
        selectedCompany = company;
        updateCompanyDropdownUI(company);
        filterJobs();
    }
    
    function selectLocation(location) {
        selectedLocation = location;
        updateLocationDropdownUI(location);
        filterJobs();
    }
    
    function updateCompanyDropdownUI(company) {
        // Update button text
        companyDropdownBtn.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon">
                <path d="M19 21V5a2 2 0 0 0-2-2H7a2 2 0 0 0-2 2v16"></path>
                <path d="M1 21h22"></path>
                <path d="M9 9h6"></path>
                <path d="M9 13h6"></path>
                <path d="M9 17h6"></path>
            </svg>
            ${company === 'all' ? 'All Companies' : company.charAt(0).toUpperCase() + company.slice(1)}
        `;
        
        // Update selected state in dropdown
        document.querySelectorAll('#company-dropdown .dropdown-item').forEach(item => {
            if (item.dataset.value === company) {
                item.classList.add('selected');
            } else {
                item.classList.remove('selected');
            }
        });
        
        // Close dropdown
        document.getElementById('company-dropdown').parentElement.classList.remove('active');
    }
    
    function updateLocationDropdownUI(location) {
        // Update button text
        locationDropdownBtn.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon">
                <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"></path>
                <circle cx="12" cy="10" r="3"></circle>
            </svg>
            ${location === 'all' ? 'All Locations' : location}
        `;
        
        // Update selected state in dropdown
        document.querySelectorAll('#location-dropdown .dropdown-item').forEach(item => {
            if (item.dataset.value === location) {
                item.classList.add('selected');
            } else {
                item.classList.remove('selected');
            }
        });
        
        // Close dropdown
        document.getElementById('location-dropdown').parentElement.classList.remove('active');
    }
    
    function handleSearch() {
        // Add a small delay to prevent excessive filtering
        clearTimeout(window.searchTimeout);
        window.searchTimeout = setTimeout(filterJobs, 300);
    }
    
    function filterJobs() {
        const searchTerm = searchInput.value.toLowerCase();
        
        // Reset to first page when filters change
        currentPage = 1;
        
        // Apply filters
        filteredJobs = allJobs.filter(job => {
            // Company filter
            if (selectedCompany !== 'all' && job.company !== selectedCompany) {
                return false;
            }
            
            // Location filter
            if (selectedLocation !== 'all' && job.Location !== selectedLocation) {
                return false;
            }
            
            // Search term filter (check title and description)
            if (searchTerm) {
                const titleMatch = job.Title && job.Title.toLowerCase().includes(searchTerm);
                const locationMatch = job.Location && job.Location.toLowerCase().includes(searchTerm);
                const descriptionMatch = job["Bullet Fields"] && 
                    job["Bullet Fields"].some(bullet => 
                        bullet.toLowerCase().includes(searchTerm)
                    );
                const companyMatch = job.company && job.company.toLowerCase().includes(searchTerm);
                    
                if (!titleMatch && !locationMatch && !descriptionMatch && !companyMatch) {
                    return false;
                }
            }
            
            return true;
        });
        
        // Render the filtered jobs
        renderJobs();
    }
    
    function toggleTheme() {
        const isDark = document.body.classList.toggle('dark-theme');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
    }
    
    function renderJobs() {
        // Calculate pagination
        const startIndex = (currentPage - 1) * jobsPerPage;
        const endIndex = startIndex + jobsPerPage;
        const paginatedJobs = filteredJobs.slice(startIndex, endIndex);
        const maxPages = Math.ceil(filteredJobs.length / jobsPerPage);
        
        // Update pagination UI
        prevPageBtn.disabled = currentPage === 1;
        nextPageBtn.disabled = currentPage === maxPages || maxPages === 0;
        pageInfoEl.textContent = `Page ${currentPage} of ${maxPages || 1}`;
        
        // Clear previous jobs
        jobsContainer.innerHTML = '';
        
        // Display message if no jobs found
        if (paginatedJobs.length === 0) {
            jobsContainer.innerHTML = `
                <div class="no-jobs-message">
                    <h3>No jobs found</h3>
                    <p>Try adjusting your filters or search terms.</p>
                </div>
            `;
            return;
        }
        
        // Render each job
        paginatedJobs.forEach(job => {
            const jobCard = document.createElement('div');
            jobCard.className = `job-card ${job.company}`;
            
            // Format bullet points if they exist
            let bulletHTML = '';
            if (job["Bullet Fields"] && Array.isArray(job["Bullet Fields"])) {
                // Limit to first 3 bullet points
                const limitedBullets = job["Bullet Fields"].slice(0, 3);
                bulletHTML = limitedBullets.map(bullet => `<li>${bullet}</li>`).join('');
            }
            
            jobCard.innerHTML = `
                <div class="job-company">
                    <img src="${companyLogos[job.company]}" alt="${job.company} logo" class="company-logo">
                    <span class="company-name">${job.company}</span>
                </div>
                <h3 class="job-title">${job.Title || 'Unknown Title'}</h3>
                <div class="job-location">
                    <i class="fas fa-map-marker-alt"></i>
                    <span>${job.Location || 'Remote/Various'}</span>
                </div>
                <div class="job-date">
                    <i class="fas fa-calendar-alt"></i>
                    <span>${job["Posted Date"] || 'Unknown date'}</span>
                </div>
                ${bulletHTML ? `<div class="job-details"><ul>${bulletHTML}</ul></div>` : ''}
                <div class="job-url">
                    <a href="${job["Job URL"]}" target="_blank">View Job <i class="fas fa-external-link-alt"></i></a>
                </div>
            `;
            
            jobsContainer.appendChild(jobCard);
        });
    }
});

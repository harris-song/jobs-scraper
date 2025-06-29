document.addEventListener('DOMContentLoaded', function() {
    // Global variables
    let allJobs = [];
    let filteredJobs = [];
    let uniqueLocations = new Set();
    let currentPage = 1;
    const jobsPerPage = 15;
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
    
    // Job line template
    const jobLineTemplate = document.getElementById('job-line-template');
    
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
        const isActive = dropdown.classList.contains('active');
        
        // Close all dropdowns first
        document.querySelectorAll('.dropdown').forEach(d => d.classList.remove('active'));
        
        // Toggle the clicked dropdown
        if (!isActive) {
            dropdown.classList.add('active');
        }
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
            <span class="material-icons">business</span>
            ${company === 'all' ? 'All Companies' : company.charAt(0).toUpperCase() + company.slice(1)}
            <span class="material-icons dropdown-arrow">expand_more</span>
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
            <span class="material-icons">location_on</span>
            ${location === 'all' ? 'All Locations' : location}
            <span class="material-icons dropdown-arrow">expand_more</span>
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
        
        // Render each job using template
        paginatedJobs.forEach(job => {
            // Clone the template
            const jobLine = jobLineTemplate.content.cloneNode(true).querySelector('.job-line');
            
            // Set company specific attributes
            jobLine.setAttribute('data-company', job.company);
            
            // Set logo
            const logoImg = jobLine.querySelector('.company-logo');
            logoImg.src = companyLogos[job.company];
            logoImg.alt = `${job.company} logo`;
            
            // Set company name
            jobLine.querySelector('.company-name').textContent = job.company.charAt(0).toUpperCase() + job.company.slice(1);
            
            // Set job title
            const jobTitle = jobLine.querySelector('.job-title');
            jobTitle.textContent = job.Title || 'Unknown Title';
            
            // Check if job was posted recently and add "New" badge
            if (job["Posted Date"] && (
                job["Posted Date"].includes("Today") || 
                job["Posted Date"].includes("Yesterday") ||
                job["Posted Date"].includes("hours ago") ||
                job["Posted Date"].includes("Just posted")
            )) {
                const newBadge = document.createElement('span');
                newBadge.className = 'new-badge';
                newBadge.textContent = 'New';
                jobTitle.appendChild(newBadge);
            }
            
            // Set location
            const locationSpan = jobLine.querySelector('.job-location span');
            locationSpan.textContent = job.Location || 'Remote/Various';
            
            // Set date
            jobLine.querySelector('.job-date').textContent = job["Posted Date"] || 'Unknown date';
            
            // Set job URL
            const jobLink = jobLine.querySelector('.job-line-actions a');
            jobLink.href = job["Job URL"] || '#';
            
            // Add to container
            jobsContainer.appendChild(jobLine);
        });
    }
    
    // Helper function to check if a string represents a recent date
    function isRecentDate(dateStr) {
        if (!dateStr) return false;
        
        const lowerDateStr = dateStr.toLowerCase();
        return lowerDateStr.includes('today') || 
               lowerDateStr.includes('yesterday') ||
               lowerDateStr.includes('hours ago') ||
               lowerDateStr.includes('just posted');
    }
});

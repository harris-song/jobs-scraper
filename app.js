document.addEventListener('DOMContentLoaded', function() {
    // Global variables
    let allJobs = [];
    let uniqueLocations = new Set();
    let jobsTable; // DataTables instance
    
    // Get DOM elements
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
    const loadingSpinner = document.getElementById('loading-spinner');
    const themeToggle = document.getElementById('theme-toggle');
    
    // Initialize theme from localStorage or system preference
    initTheme();
    
    // Company logo URLs
    const companyLogosLight = {
        accenture: 'https://upload.wikimedia.org/wikipedia/commons/c/cd/Accenture.svg',
        apple: 'https://upload.wikimedia.org/wikipedia/commons/f/fa/Apple_logo_black.svg',
        meta: 'https://upload.wikimedia.org/wikipedia/commons/7/7b/Meta_Platforms_Inc._logo.svg',
        nvidia: 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ6E96zjEpu_8FhoCCl_myMlu86D49-g_b1MA&s',
        salesforce: 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTE-Pu_DrwbVA66DDPZ_HuVY2WztlN193pOxw&s',
        tesla: 'https://upload.wikimedia.org/wikipedia/commons/e/e8/Tesla_logo.png'
    };
    
    // Company logo URLs for dark mode
    const companyLogosDark = {
        accenture: 'https://companieslogo.com/img/orig/ACN_BIG.D-871a76ce.png?t=1720244490', // This should be more visible in dark mode
        apple: 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Apple_gray_logo.png/500px-Apple_gray_logo.png',
        meta: 'https://crystalpng.com/wp-content/uploads/2025/02/meta_logo.png',
        nvidia: 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ6E96zjEpu_8FhoCCl_myMlu86D49-g_b1MA&s',
        salesforce: 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTE-Pu_DrwbVA66DDPZ_HuVY2WztlN193pOxw&s',
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
            
            // Update stats
            updateStats();
            
            // Initialize DataTable
            initDataTable();
            
            // Setup custom filters for DataTables
            setupCustomFilters();
            
            // Hide loading spinner
            loadingSpinner.style.display = 'none';
            
            // Add event listener for theme toggle
            themeToggle.addEventListener('click', toggleTheme);
            
        } catch (error) {
            console.error('Error initializing app:', error);
            document.querySelector('.table-container').innerHTML = `<div class="error-message">
                <h3>Failed to load job data</h3>
                <p>${error.message}</p>
            </div>`;
            loadingSpinner.style.display = 'none';
        }
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
    
    function initDataTable() {
        // Format jobs data for DataTable
        const tableData = allJobs.map(job => {
            // Select the appropriate logo based on theme
            const isDarkMode = document.body.classList.contains('dark-theme');
            const logoSrc = isDarkMode ? companyLogosDark[job.company] : companyLogosLight[job.company];
            
            // Create company logo cell
            const companyLogo = `<img src="${logoSrc}" alt="${job.company} logo" class="company-logo">`;
            
            // Format company name with first letter capitalized
            const companyName = job.company.charAt(0).toUpperCase() + job.company.slice(1);
            
            // Combine logo and company name
            const company = `<div class="company-cell">${companyLogo} <span>${companyName}</span></div>`;
            
            // Format job title with "New" badge if recent
            let title = job.Title || 'Unknown Title';
            if (isRecentDate(job["Posted Date"])) {
                title = `${title} <span class="new-badge">New</span>`;
            }
            
            // Format location with icon
            const location = `<span class="job-location"><span class="material-icons">location_on</span> ${job.Location || 'Remote/Various'}</span>`;
            
            // Format date
            const date = job["Posted Date"] || 'Unknown date';
            
            // Format action button with academicpages style
            const action = `<a href="${job["Job URL"] || '#'}" target="_blank" class="btn-primary">
                <span class="material-icons" style="font-size: 0.9em; margin-right: 3px;">open_in_new</span> View
            </a>`;
            
            return [company, title, location, date, action];
        });
        
        // Initialize DataTable
        jobsTable = $('#jobs-table').DataTable({
            data: tableData,
            columnDefs: [
                { className: "dt-center", targets: [0, 2, 3, 4] },
                { className: "dt-body-left", targets: 1 },
                // Adjust column widths for better spacing
                { width: "15%", targets: 0 }, // Company column
                { width: "35%", targets: 1 }, // Title column
                { width: "20%", targets: 2 }, // Location column  
                { width: "20%", targets: 3 }, // Date column
                { width: "10%", targets: 4 }  // Actions column
            ],
            responsive: {
                details: false  // Disable the responsive details feature that hides columns
            },
            scrollX: false,     // Disable horizontal scrolling to prevent scroll wheels
            pageLength: 25,     // Show 25 rows per page as requested
            dom: '<"top"if>rt<"bottom"lp><"clear">',
            ordering: true,
            stripeClasses: ['even-row', 'odd-row'],
            hover: true,
            language: {
                search: "_INPUT_",
                searchPlaceholder: "Search jobs...",
                lengthMenu: "_MENU_ per page",
                info: "Showing _START_ to _END_ of _TOTAL_ jobs",
                infoEmpty: "Showing 0 to 0 of 0 jobs",
                infoFiltered: "(filtered from _MAX_ total jobs)"
            }
        });
        
        // Replace the default search input with our custom one
        $('#jobs-table_filter').hide();
        
        // Connect our existing search box to DataTable search
        $('#search-input').on('keyup', function() {
            jobsTable.search(this.value).draw();
        });
        
        // Setup custom filtering for DataTables
        setupCustomFilters();
    }
    
    // Setup custom filtering for DataTables
    function setupCustomFilters() {
        // Company filter
        document.querySelectorAll('#company-dropdown .dropdown-item').forEach(item => {
            item.addEventListener('click', function() {
                const company = this.dataset.value;
                
                // Update dropdown button text
                companyDropdownBtn.innerHTML = `
                    <span class="material-icons">business</span>
                    ${company === 'all' ? 'All Companies' : company.charAt(0).toUpperCase() + company.slice(1)}
                    <span class="material-icons dropdown-arrow">expand_more</span>
                `;
                
                // Update selected state in dropdown
                document.querySelectorAll('#company-dropdown .dropdown-item').forEach(item => {
                    item.classList.toggle('selected', item.dataset.value === company);
                });
                
                // Apply filter to DataTable - ensure all companies option works
                if (company === 'all') {
                    jobsTable.column(0).search('').draw();
                } else {
                    // Use regex false for exact match with company name in cell
                    jobsTable.column(0).search(company, true, false).draw();
                }
                
                // Close dropdown
                document.getElementById('company-dropdown').parentElement.classList.remove('active');
            });
        });
        
        // Company dropdown toggle
        companyDropdownBtn.addEventListener('click', function() {
            toggleDropdown('company');
        });
        
        // Populate location filter dropdown
        populateLocationFilter();
        
        // Location dropdown toggle
        locationDropdownBtn.addEventListener('click', function() {
            toggleDropdown('location');
        });
        
        // Close dropdowns when clicking outside
        document.addEventListener('click', (event) => {
            if (!event.target.closest('.dropdown')) {
                document.querySelectorAll('.dropdown').forEach(dropdown => {
                    dropdown.classList.remove('active');
                });
            }
        });
    }
    
    function populateLocationFilter() {
        // First, ensure the "All Locations" option has the proper click event handler
        const allLocationsItem = document.querySelector('#location-dropdown .dropdown-item[data-value="all"]');
        if (allLocationsItem) {
            allLocationsItem.addEventListener('click', function() {
                // Update dropdown button text
                locationDropdownBtn.innerHTML = `
                    <span class="material-icons">location_on</span>
                    All Locations
                    <span class="material-icons dropdown-arrow">expand_more</span>
                `;
                
                // Update selected state in dropdown
                document.querySelectorAll('#location-dropdown .dropdown-item').forEach(item => {
                    item.classList.toggle('selected', item.dataset.value === 'all');
                });
                
                // Clear any location filter
                jobsTable.column(2).search('').draw();
                
                // Close dropdown
                document.getElementById('location-dropdown').parentElement.classList.remove('active');
            });
        }
        
        // Sort locations alphabetically
        const sortedLocations = Array.from(uniqueLocations).sort();
        
        // Add options to location dropdown
        sortedLocations.forEach(location => {
            const item = document.createElement('div');
            item.className = 'dropdown-item';
            item.dataset.value = location;
            item.textContent = location;
            
            // Add click event for filtering
            item.addEventListener('click', function() {
                const location = this.dataset.value;
                
                // Update dropdown button text
                locationDropdownBtn.innerHTML = `
                    <span class="material-icons">location_on</span>
                    ${location}
                    <span class="material-icons dropdown-arrow">expand_more</span>
                `;
                
                // Update selected state in dropdown
                document.querySelectorAll('#location-dropdown .dropdown-item').forEach(item => {
                    item.classList.toggle('selected', item.dataset.value === location);
                });
                
                // Apply filter to DataTable
                jobsTable.column(2).search(location, true, false).draw();
                
                // Close dropdown
                document.getElementById('location-dropdown').parentElement.classList.remove('active');
            });
            
            locationDropdown.appendChild(item);
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
            
            // For debugging
            console.log(`${type} dropdown opened`);
            
            // Make sure dropdown is positioned correctly
            const dropdownContent = document.getElementById(`${type}-dropdown`);
            dropdownContent.style.display = 'block';
            
            // Ensure event listeners are properly attached
            if (type === 'company') {
                // Check if all companies item has event listener
                const allCompaniesItem = document.querySelector('#company-dropdown .dropdown-item[data-value="all"]');
                if (allCompaniesItem) {
                    console.log('All Companies item found');
                }
            } else if (type === 'location') {
                // Check if all locations item has event listener
                const allLocationsItem = document.querySelector('#location-dropdown .dropdown-item[data-value="all"]');
                if (allLocationsItem) {
                    console.log('All Locations item found');
                }
            }
        }
    }
    
    function toggleTheme() {
        const isDark = document.body.classList.toggle('dark-theme');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
        
        // Refresh DataTable with new logos based on theme
        if (jobsTable) {
            // Destroy the current table
            jobsTable.destroy();
            
            // Reinitialize the table with the current theme
            initDataTable();
        }
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

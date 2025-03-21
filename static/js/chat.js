let sessionActive = true; // Since files are loaded from backend, we start with active session

// Configure marked options
marked.setOptions({
    highlight: function(code, language) {
        if (language && hljs.getLanguage(language)) {
            try {
                return hljs.highlight(code, { language }).value;
            } catch (err) {}
        }
        return code;
    },
    breaks: true,
    gfm: true
});

function addMessage(message, isUser = false) {
    const messagesDiv = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
    
    // Create message header
    const headerDiv = document.createElement('div');
    headerDiv.className = 'message-header';
    
    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'message-avatar';
    avatarDiv.style.background = isUser ? 'var(--message-user-bg)' : 'var(--accent-color)';
    avatarDiv.textContent = isUser ? 'You' : 'AI';
    
    const nameSpan = document.createElement('span');
    nameSpan.textContent = isUser ? 'You' : 'Assistant';
    
    headerDiv.appendChild(avatarDiv);
    headerDiv.appendChild(nameSpan);
    messageDiv.appendChild(headerDiv);
    
    // Create message content
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    if (isUser) {
        contentDiv.textContent = message;
    } else {
        contentDiv.innerHTML = marked.parse(message);
        // Initialize syntax highlighting for code blocks
        contentDiv.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
        });
    }
    
    messageDiv.appendChild(contentDiv);
    messagesDiv.appendChild(messageDiv);
    
    // Smooth scroll to bottom
    messagesDiv.scrollTo({
        top: messagesDiv.scrollHeight,
        behavior: 'smooth'
    });
}

function showTypingIndicator() {
    document.getElementById('typing-indicator').style.display = 'block';
    const messagesDiv = document.getElementById('chat-messages');
    messagesDiv.scrollTo({
        top: messagesDiv.scrollHeight,
        behavior: 'smooth'
    });
}

function hideTypingIndicator() {
    document.getElementById('typing-indicator').style.display = 'none';
}

async function sendQuery() {
    const queryInput = document.getElementById('query-input');
    const sendButton = document.querySelector('.send-button');
    const query = queryInput.value.trim();
    
    if (!query) return;

    // Disable input while processing
    queryInput.disabled = true;
    sendButton.disabled = true;

    addMessage(query, true);
    queryInput.value = '';
    
    showTypingIndicator();

    try {
        const response = await fetch('/process-query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query: query })
        });

        const data = await response.json();
        hideTypingIndicator();
        
        if (response.ok) {
            addMessage(data.response, false);
        } else {
            addMessage(`Error: ${data.detail}`, false);
        }
    } catch (error) {
        hideTypingIndicator();
        addMessage('Error processing query: ' + error.message, false);
    } finally {
        // Re-enable input
        queryInput.disabled = false;
        sendButton.disabled = false;
        queryInput.focus();
    }
}

// Handle Enter key in input
document.getElementById('query-input').addEventListener('keypress', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendQuery();
    }
});

// Clean up when window closes
window.addEventListener('beforeunload', async () => {
    if (sessionActive) {
        try {
            await fetch('/cleanup', { method: 'POST' });
        } catch (error) {
            console.error('Error during cleanup:', error);
        }
    }
});

document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('companyModal');
    const companyList = document.getElementById('companyList');
    const searchInput = document.getElementById('companySearch');

    // Show modal when page loads
    showCompanyModal();

    // Fetch companies when modal opens
    function showCompanyModal() {
        modal.style.display = 'block';
        fetchCompanies();
    }

    // Fetch companies from the API
    async function fetchCompanies() {
        try {
            const response = await fetch('/get_companies');
            const companies = await response.json();
            displayCompanies(companies);
        } catch (error) {
            console.error('Error fetching companies:', error);
        }
    }

    // Display companies in the modal
    function displayCompanies(companies) {
        companyList.innerHTML = '';
        companies.forEach(company => {
            const li = document.createElement('li');
            li.textContent = company;
            li.onclick = () => selectCompany(company);
            companyList.appendChild(li);
        });
    }

    // Handle company selection
    async function selectCompany(company) {
        try {
            const response = await fetch('/get_company_values', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ company: company })
            });
            const data = await response.json();
            
            // Handle the response data as needed
            modal.style.display = 'none';
            
            // You might want to update the UI to show the selected company
            // For example, update the header title
            document.querySelector('.header-title h1').textContent = `Enterprise PDF Assistant - ${company}`;
        } catch (error) {
            console.error('Error fetching company values:', error);
        }
    }

    // Handle search functionality
    searchInput.addEventListener('input', function(e) {
        const searchTerm = e.target.value.toLowerCase();
        const items = companyList.getElementsByTagName('li');
        
        Array.from(items).forEach(item => {
            const text = item.textContent.toLowerCase();
            item.style.display = text.includes(searchTerm) ? '' : 'none';
        });
    });
}); 
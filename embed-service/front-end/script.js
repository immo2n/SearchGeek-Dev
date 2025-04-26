async function filterData(response) {
    const mainQuery = response.query;
    const docs = response.results;
    const scores = response.scores;

    const prompt = `You are an intelligent assistant helping a user select the most relevant product based on their search intent.
    
    User Intent:
    "${mainQuery}"
    
    Here are the top 3 product results from the vector database, including their relevance scores:
    
    ${docs[0].map((doc, idx) => `Result ${idx + 1} (Score: ${scores[0][idx]}): ${doc}`).join("\n\n")}
    
    Instructions:
    - Identify the single most relevant product based on the *highest score*.
    - Extract key information directly from that product description.
    - Do NOT infer or hallucinate missing data.
    - Respond with a single, clear sentence recommending the best product to buy based on the user's intent.
    - Wrap your response in this exact JSON format: { "response": "<your one-sentence recommendation here>" }`;    

    console.log("Alanyzing the data with the intent and the results...");
    const responseText = await fetch('http://localhost:8002/generate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ prompt })
    });
    if (!responseText.ok) {
        throw new Error('Failed to fetch search results');
    }
    const data = await responseText.json();
    const searchResults = document.getElementById('searchResults');
    searchResults.textContent = `Filtered Data:\n${JSON.stringify(data, null, 2)}`;
    console.log("Filtered Data: ", data);
}

async function searchVector(intentData, query) {
    console.log("Intent Data: ", intentData);
    console.log("Query: ", query);

    // Define the body of the request based on the intentData
    const requestBody = {
        primary_intent: intentData.primary_intent,
        brand: intentData.brand || "",  // If brand is not provided, default to empty string
        product_type: intentData.product_type,
        desired_attributes: intentData.desired_attributes,
        constraints: intentData.constraints
    };

    try {
        // Send the request to the backend API
        const response = await fetch('http://localhost:8001/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)  // Send the request body as JSON
        });

        // Check if the response is OK
        if (!response.ok) {
            throw new Error('Failed to fetch search results');
        }

        // Parse the response data
        const data = await response.json();

        // Log the results for debugging
        console.log("Search Results: ", data);

        filterData(data);

        // Format the results and display them (for example, in the UI)
        const resultsText = data.results.map((doc, idx) => `Result ${idx + 1}: ${doc}`).join("\n");
        // Assuming you have a container to display the results
        const searchResults = document.getElementById('searchResults');  // Update with your actual element ID
        searchResults.textContent = searchResults.textContent + `\nSearch Results:\n${resultsText} \n data: ${JSON.stringify(data, null, 2)}`;

    } catch (error) {
        // Handle any errors
        const searchResults = document.getElementById('searchResults');  // Update with your actual element ID
        searchResults.textContent = `Error: ${error.message}`;
    }
}

async function generateEmbedding() {
    const lastSent = document.getElementById('lastSent');
    const productData = document.getElementById('productData').value;
    const embeddingResult = document.getElementById('embeddingResult');

    embeddingResult.textContent = 'Loading...';

    if (!productData) {
        embeddingResult.textContent = 'Product data is required!';
        return;
    }

    try {
        const response = await fetch('http://localhost:8001/embed', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                texts: [productData]
            })
        });

        if (!response.ok) {
            throw new Error('Failed to fetch embeddings');
        }

        const data = await response.json();
        lastSent.textContent = `Last sent: ${productData}`;
        embeddingResult.textContent = `Embedding:\n${JSON.stringify(data.embeddings, null, 2)}\n\nID: ${data.ids[0]}`;

    } catch (error) {
        embeddingResult.textContent = `Error: ${error.message}`;
    }
}

async function checkCount() {
    const embeddingResult = document.getElementById('embeddingResult');
    embeddingResult.textContent = 'Loading...';

    try {
        const response = await fetch('http://localhost:8001/count');
        if (!response.ok) {
            throw new Error('Failed to fetch count');
        }
        const data = await response.json();
        embeddingResult.textContent = `Document count: ${data.count}`;
    } catch (error) {
        embeddingResult.textContent = `Error: ${error.message}`;
    }
}

async function getAll() {
    const embeddingResult = document.getElementById('embeddingResult');
    embeddingResult.textContent = 'Loading...';

    try {
        const response = await fetch('http://localhost:8001/get_all');
        if (!response.ok) {
            throw new Error('Failed to fetch data');
        }
        const data = await response.json();
        embeddingResult.textContent = `All data:\n${JSON.stringify(data, null, 2)}`;
    } catch (error) {
        embeddingResult.textContent = `Error: ${error.message}`;
    }
}

async function searchDocuments() {
    const searchQuery = document.getElementById('searchQuery').value;
    const searchResults = document.getElementById('searchResults');

    searchResults.textContent = 'Loading... Trying to filter the intent of the user';

    if (!searchQuery) {
        searchResults.textContent = 'Search query is required!';
        return;
    }

    try {
        const promptText = `You are an intelligent assistant. A user has searched the following phrase: "${searchQuery}".

Analyze the query carefully and classify it into these categories:
- Primary Intent
- Product Type
- Desired Attributes
- Constraints
- Brand

Important rules:
- Only include specific, meaningful attributes (e.g., "High Resolution", "Waterproof", "10GB RAM").
- Do NOT include vague, generic, or common words (e.g., "one", "good", "best", "cheap", "the").
- If the user explicitly mentions a brand (e.g., "HP", "Apple"), extract it and set it as "Brand".
- If the user does NOT mention any brand, set "Brand" to an empty string "".
- For "Constraints", if the user mentions a budget or specific limits, include them.
- Only include information that is directly present in the user's query.

Respond ONLY with a valid JSON object in this format:

{
  "primary_intent": "<value>",
  "brand": "<value>",
  "product_type": "<value>",
  "desired_attributes": ["<value>", "<value>"],
  "constraints": ["<value>", "<value>"]
}

Do not include any explanation, apology, or text outside the JSON.`;

        const response = await fetch('http://localhost:8002/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ prompt: promptText })
        });

        if (!response.ok) {
            throw new Error('Failed to fetch search results');
        }

        const data = await response.json();
        searchResults.textContent = `Intent Filter result:\n${JSON.stringify(data, null, 2)} \n Procedding to search the vector database...`;

        searchVector(data.response, searchQuery);

    } catch (error) {
        searchResults.textContent = `Error: ${error.message}`;
    }
}
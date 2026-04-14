const movieInput = document.getElementById("movieInput");
const recommendBtn = document.getElementById("recommendBtn");
const message = document.getElementById("message");
const results = document.getElementById("results");

function setMessage(text, type = "") {
  message.textContent = text;
  message.classList.remove("error", "success");
  if (type) {
    message.classList.add(type);
  }
}

function renderRecommendations(items) {
  results.innerHTML = "";

  items.forEach((movie, index) => {
    const card = document.createElement("article");
    card.className = "card";
    card.style.animationDelay = `${index * 70}ms`;

    const image = document.createElement("img");
    image.className = "poster";
    image.src = movie.poster;
    image.alt = `${movie.title} poster`;
    image.loading = "lazy";

    const heading = document.createElement("p");
    heading.className = "card-title";
    heading.textContent = movie.title;

    card.appendChild(image);
    card.appendChild(heading);
    results.appendChild(card);
  });
}

async function fetchRecommendations() {
  const movie = movieInput.value.trim();
  if (!movie) {
    setMessage("Please choose a movie title first.", "error");
    return;
  }

  setMessage("Searching for similar movies...");
  recommendBtn.disabled = true;
  recommendBtn.textContent = "Loading...";

  try {
    const response = await fetch("/recommend", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ movie })
    });

    const data = await response.json();

    if (!response.ok || !data.ok) {
      setMessage(data.error || "Could not generate recommendations.", "error");
      results.innerHTML = "";
      return;
    }

    renderRecommendations(data.recommendations);
    setMessage(`Top picks similar to \"${data.movie}\"`, "success");
  } catch (error) {
    setMessage("Network error while requesting recommendations.", "error");
    results.innerHTML = "";
  } finally {
    recommendBtn.disabled = false;
    recommendBtn.textContent = "Find Matches";
  }
}

recommendBtn.addEventListener("click", fetchRecommendations);
movieInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    fetchRecommendations();
  }
});

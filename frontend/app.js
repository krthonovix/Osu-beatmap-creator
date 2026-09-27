let uploadedAudioToken = null;
let selectedStyleId = "jump";
let currentMappers = [];

// Elementos del DOM
const dropzone = document.getElementById("dropzone");
const audioFileInput = document.getElementById("audioFileInput");
const fileNamePreview = document.getElementById("fileNamePreview");
const analysisPanel = document.getElementById("analysisPanel");
const statBpm = document.getElementById("statBpm");
const statDuration = document.getElementById("statDuration");
const metaTitle = document.getElementById("metaTitle");
const metaArtist = document.getElementById("metaArtist");

const starSlider = document.getElementById("starSlider");
const starValueBadge = document.getElementById("starValueBadge");
const valAr = document.getElementById("valAr");
const valCs = document.getElementById("valCs");
const valOd = document.getElementById("valOd");
const valHp = document.getElementById("valHp");

const stylesGrid = document.getElementById("stylesGrid");
const mapperSelect = document.getElementById("mapperSelect");
const mapperDescription = document.getElementById("mapperDescription");
const btnGenerate = document.getElementById("btnGenerate");

const progressModal = document.getElementById("progressModal");
const progressBarFill = document.getElementById("progressBarFill");
const progressPercentage = document.getElementById("progressPercentage");
const statusMessage = document.getElementById("statusMessage");
const downloadSection = document.getElementById("downloadSection");
const btnDownload = document.getElementById("btnDownload");
const btnCloseModal = document.getElementById("btnCloseModal");

// Inicialización
document.addEventListener("DOMContentLoaded", async () => {
  await loadOptions();
  updateDifficultyStats(parseFloat(starSlider.value));
  setupEvents();
});

async function loadOptions() {
  try {
    const res = await fetch("/api/options");
    const data = await res.json();
    
    // Render estilos
    stylesGrid.innerHTML = "";
    data.styles.forEach((s, idx) => {
      const card = document.createElement("div");
      card.className = `style-card ${s.id === selectedStyleId ? "selected" : ""}`;
      card.innerHTML = `
        <span class="style-name">${s.name}</span>
        <span class="style-desc">${s.description}</span>
      `;
      card.onclick = () => {
        document.querySelectorAll(".style-card").forEach(c => c.classList.remove("selected"));
        card.classList.add("selected");
        selectedStyleId = s.id;
      };
      stylesGrid.appendChild(card);
    });

    // Render mappers
    currentMappers = data.mappers;
    mapperSelect.innerHTML = "";
    data.mappers.forEach(m => {
      const opt = document.createElement("option");
      opt.value = m.id;
      opt.textContent = `${m.name} ${m.mapper_id ? `(#${m.mapper_id})` : ""}`;
      if (m.id === "sotarks") opt.selected = true;
      mapperSelect.appendChild(opt);
    });
    updateMapperDescription();

  } catch (err) {
    console.error("Error cargando opciones:", err);
  }
}

function updateMapperDescription() {
  const selected = currentMappers.find(m => m.id === mapperSelect.value);
  if (selected) {
    mapperDescription.textContent = selected.description;
  }
}

mapperSelect.addEventListener("change", updateMapperDescription);

function formatTime(seconds) {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s < 10 ? "0" : ""}${s}`;
}

function updateDifficultyStats(stars) {
  starValueBadge.textContent = `${stars.toFixed(1)} ★`;
  
  let ar, cs, od, hp;
  if (stars <= 3.0) {
    ar = (6.0 + (stars - 1.0) * 0.75).toFixed(1);
    cs = "3.5";
    od = (5.0 + (stars - 1.0) * 1.0).toFixed(1);
    hp = "3.5";
  } else if (stars <= 5.0) {
    ar = (7.5 + (stars - 3.0) * 0.65).toFixed(1);
    cs = "4.0";
    od = (7.0 + (stars - 3.0) * 0.75).toFixed(1);
    hp = "5.0";
  } else if (stars <= 7.0) {
    ar = (8.8 + (stars - 5.0) * 0.35).toFixed(1);
    cs = "4.2";
    od = (8.5 + (stars - 5.0) * 0.35).toFixed(1);
    hp = "5.0";
  } else {
    ar = Math.min(10.0, 9.5 + (stars - 7.0) * 0.17).toFixed(1);
    cs = stars < 8.0 ? "4.2" : "4.4";
    od = Math.min(10.0, 9.2 + (stars - 7.0) * 0.27).toFixed(1);
    hp = "5.5";
  }

  valAr.textContent = ar;
  valCs.textContent = cs;
  valOd.textContent = od;
  valHp.textContent = hp;
}

starSlider.addEventListener("input", (e) => {
  updateDifficultyStats(parseFloat(e.target.value));
});

// Drag & Drop
function setupEvents() {
  dropzone.onclick = () => audioFileInput.click();

  dropzone.ondragover = (e) => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  };

  dropzone.ondragleave = () => {
    dropzone.classList.remove("dragover");
  };

  dropzone.ondrop = (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
    if (e.dataTransfer.files.length > 0) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  audioFileInput.onchange = (e) => {
    if (e.target.files.length > 0) {
      handleFile(e.target.files[0]);
    }
  };
}

async function handleFile(file) {
  if (!file) return;

  fileNamePreview.textContent = `Analizando: ${file.name}...`;
  dropzone.style.opacity = "0.7";

  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch("/api/analyze", {
      method: "POST",
      body: formData
    });

    if (!res.ok) throw new Error("Error al analizar audio");
    const data = await res.json();

    uploadedAudioToken = data.audio_token;
    fileNamePreview.textContent = `Archivo: ${data.filename}`;
    statBpm.textContent = `${data.bpm} BPM`;
    statDuration.textContent = formatTime(data.duration);
    metaTitle.value = data.title;
    metaArtist.value = data.artist;

    analysisPanel.classList.remove("hidden");
    btnGenerate.disabled = false;
    dropzone.style.opacity = "1";

  } catch (err) {
    fileNamePreview.textContent = `Error al procesar archivo: ${err.message}`;
    dropzone.style.opacity = "1";
  }
}

// Iniciar Generación
btnGenerate.onclick = async () => {
  if (!uploadedAudioToken) return;

  // Abrir modal
  progressModal.classList.remove("hidden");
  downloadSection.classList.add("hidden");
  progressBarFill.style.width = "5%";
  progressPercentage.textContent = "5%";
  statusMessage.textContent = "Enviando parámetros al motor de difusión...";

  const formData = new FormData();
  formData.append("audio_token", uploadedAudioToken);
  formData.append("difficulty", starSlider.value);
  formData.append("style_id", selectedStyleId);
  formData.append("mapper_id", mapperSelect.value);
  formData.append("title", metaTitle.value.trim());
  formData.append("artist", metaArtist.value.trim());

  try {
    const res = await fetch("/api/generate", {
      method: "POST",
      body: formData
    });

    if (!res.ok) throw new Error("Fallo al iniciar el trabajo de generación");
    const data = await res.json();
    const jobId = data.job_id;

    // Escuchar progreso en tiempo real con SSE
    const eventSource = new EventSource(`/api/events/${jobId}`);

    eventSource.onmessage = (e) => {
      const job = JSON.parse(e.data);
      progressBarFill.style.width = `${job.progress}%`;
      progressPercentage.textContent = `${job.progress}%`;
      statusMessage.textContent = job.message;

      if (job.status === "completed") {
        eventSource.close();
        downloadSection.classList.remove("hidden");
        btnDownload.href = job.download_url;
      } else if (job.status === "failed") {
        eventSource.close();
        statusMessage.textContent = `❌ ${job.error || "Error desconocido durante la generación."}`;
        progressBarFill.style.background = "#ff4444";
      }
    };

    eventSource.onerror = () => {
      eventSource.close();
    };

  } catch (err) {
    statusMessage.textContent = `❌ Error: ${err.message}`;
  }
};

btnCloseModal.onclick = () => {
  progressModal.classList.add("hidden");
};

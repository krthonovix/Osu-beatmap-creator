let uploadedAudioToken = null;
let selectedStyleId = "jump";
let currentMappers = [];
let detectedBpm = 180.0;

// Elementos del DOM
const dropzone = document.getElementById("dropzone");
const audioFileInput = document.getElementById("audioFileInput");
const fileNamePreview = document.getElementById("fileNamePreview");
const analysisPanel = document.getElementById("analysisPanel");
const statDuration = document.getElementById("statDuration");
const metaTitle = document.getElementById("metaTitle");
const metaArtist = document.getElementById("metaArtist");

// BPM
const inputBpm = document.getElementById("inputBpm");
const btnRecommendBpm = document.getElementById("btnRecommendBpm");
const detectedBpmLabel = document.getElementById("detectedBpmLabel");

// Dificultad & Stats
const starSlider = document.getElementById("starSlider");
const starValueBadge = document.getElementById("starValueBadge");
const btnRecommendStats = document.getElementById("btnRecommendStats");
const recommendStarLabel = document.getElementById("recommendStarLabel");

const inputAr = document.getElementById("inputAr");
const inputCs = document.getElementById("inputCs");
const inputOd = document.getElementById("inputOd");
const inputHp = document.getElementById("inputHp");
const inputSv = document.getElementById("inputSv");

// Configuración adicional
const stylesGrid = document.getElementById("stylesGrid");
const mapperSelect = document.getElementById("mapperSelect");
const mapperDescription = document.getElementById("mapperDescription");
const btnGenerate = document.getElementById("btnGenerate");

// Modal de Progreso
const progressModal = document.getElementById("progressModal");
const progressBarFill = document.getElementById("progressBarFill");
const progressPercentage = document.getElementById("progressPercentage");
const statusMessage = document.getElementById("statusMessage");
const downloadSection = document.getElementById("downloadSection");
const btnDownload = document.getElementById("btnDownload");
const btnCloseModal = document.getElementById("btnCloseModal");

// Historial
const historyList = document.getElementById("historyList");
const historyCountBadge = document.getElementById("historyCountBadge");
const btnRefreshHistory = document.getElementById("btnRefreshHistory");

// Inicialización
document.addEventListener("DOMContentLoaded", async () => {
  await loadOptions();
  applyRecommendedStats(parseFloat(starSlider.value));
  setupEvents();
  loadHistory();
});

async function loadOptions() {
  try {
    const res = await fetch("/api/options");
    const data = await res.json();
    
    // Render estilos
    stylesGrid.innerHTML = "";
    data.styles.forEach((s) => {
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

// Cálculo canónico de valores recomendados para osu!
function getRecommendedStats(stars) {
  let ar, cs, od, hp, sv;
  
  if (stars <= 3.0) {
    ar = (6.0 + (stars - 1.0) * 0.75).toFixed(1);
    cs = "3.5";
    od = (5.0 + (stars - 1.0) * 1.0).toFixed(1);
    hp = "3.5";
    sv = "1.40";
  } else if (stars <= 5.0) {
    ar = (7.5 + (stars - 3.0) * 0.65).toFixed(1);
    cs = "4.0";
    od = (7.0 + (stars - 3.0) * 0.75).toFixed(1);
    hp = "5.0";
    sv = "1.60";
  } else if (stars <= 7.0) {
    ar = (8.8 + (stars - 5.0) * 0.35).toFixed(1);
    cs = "4.2";
    od = (8.5 + (stars - 5.0) * 0.35).toFixed(1);
    hp = "5.0";
    sv = "1.82";
  } else {
    ar = Math.min(10.0, 9.5 + (stars - 7.0) * 0.17).toFixed(1);
    cs = (stars < 8.0 ? 4.2 : 4.4).toFixed(1);
    od = Math.min(10.0, 9.2 + (stars - 7.0) * 0.27).toFixed(1);
    hp = "5.5";
    sv = (1.82 + (stars - 7.0) * 0.15).toFixed(2);
  }

  return { ar, cs, od, hp, sv };
}

// Aplica los valores recomendados a los inputs
function applyRecommendedStats(stars) {
  const stats = getRecommendedStats(stars);
  inputAr.value = stats.ar;
  inputCs.value = stats.cs;
  inputOd.value = stats.od;
  inputHp.value = stats.hp;
  inputSv.value = stats.sv;
  
  starValueBadge.textContent = `${stars.toFixed(1)} ★`;
  if (recommendStarLabel) {
    recommendStarLabel.textContent = `${stars.toFixed(1)}★`;
  }
}

// Slider de dificultad
starSlider.addEventListener("input", (e) => {
  const stars = parseFloat(e.target.value);
  applyRecommendedStats(stars);
});

// Botón de auto-recomendación de stats
if (btnRecommendStats) {
  btnRecommendStats.addEventListener("click", () => {
    const stars = parseFloat(starSlider.value);
    applyRecommendedStats(stars);
  });
}

// Botón de recomendación de BPM
if (btnRecommendBpm) {
  btnRecommendBpm.addEventListener("click", () => {
    inputBpm.value = detectedBpm;
  });
}

// Botón de refrescar historial
if (btnRefreshHistory) {
  btnRefreshHistory.addEventListener("click", loadHistory);
}

// Drag & Drop y selección de archivo
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

  fileNamePreview.textContent = `Analizando audio con librosa: ${file.name}...`;
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
    fileNamePreview.textContent = `Archivo cargado: ${data.filename}`;
    
    // Asignar BPM y permitir edición
    detectedBpm = data.bpm;
    inputBpm.value = data.bpm;
    if (detectedBpmLabel) {
      detectedBpmLabel.textContent = `${data.bpm}`;
    }

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

// Iniciar Generación con todos los parámetros personalizados
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

  // Parámetros avanzados editables
  formData.append("ar", inputAr.value);
  formData.append("cs", inputCs.value);
  formData.append("od", inputOd.value);
  formData.append("hp", inputHp.value);
  formData.append("sv", inputSv.value);
  if (inputBpm.value) {
    formData.append("bpm", inputBpm.value);
  }

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

        // Poblar reporte de dificultad oficial (rosu-pp)
        if (job.real_stars !== undefined && job.real_stars !== null) {
          const reportRealStars = document.getElementById("reportRealStars");
          const reportTargetStars = document.getElementById("reportTargetStars");
          const reportAimStars = document.getElementById("reportAimStars");
          const reportSpeedStars = document.getElementById("reportSpeedStars");
          const reportMaxCombo = document.getElementById("reportMaxCombo");
          const reportCircles = document.getElementById("reportCircles");
          const reportSliders = document.getElementById("reportSliders");
          const reportEvaluation = document.getElementById("reportEvaluation");

          if (reportRealStars) reportRealStars.textContent = `${job.real_stars.toFixed(2)} ★`;
          if (reportTargetStars) reportTargetStars.textContent = `${job.difficulty.toFixed(1)} ★`;
          if (reportAimStars) reportAimStars.textContent = `${job.aim_stars ? job.aim_stars.toFixed(2) : '--'}★`;
          if (reportSpeedStars) reportSpeedStars.textContent = `${job.speed_stars ? job.speed_stars.toFixed(2) : '--'}★`;
          if (reportMaxCombo) reportMaxCombo.textContent = `${job.max_combo || '--'}x`;
          if (reportCircles) reportCircles.textContent = `${job.circle_count || '--'}`;
          if (reportSliders) reportSliders.textContent = `${job.slider_count || '--'}`;
          if (reportEvaluation) reportEvaluation.textContent = job.difficulty_evaluation || "";
        }

        // Actualizar historial de beatmaps de inmediato
        loadHistory();

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

// Cargar y renderizar historial de beatmaps
async function loadHistory() {
  if (!historyList) return;
  try {
    const res = await fetch("/api/history");
    if (!res.ok) return;
    const items = await res.json();

    if (historyCountBadge) {
      historyCountBadge.textContent = `${items.length} ${items.length === 1 ? "mapa" : "mapas"}`;
    }

    if (!items || items.length === 0) {
      historyList.innerHTML = `<div class="history-empty">No hay beatmaps generados todavía. Crea uno arriba para que aparezca aquí.</div>`;
      return;
    }

    historyList.innerHTML = "";
    items.forEach((item) => {
      const el = document.createElement("div");
      el.className = "history-item";

      const realStarsStr = item.real_stars ? `${item.real_stars.toFixed(2)}★` : `${item.target_stars.toFixed(1)}★`;
      const bpmStr = item.bpm ? `${item.bpm} BPM` : "";
      const styleName = item.style_id ? item.style_id.toUpperCase() : "MAP";
      const mapperName = item.mapper_id || "Neutral";
      const sizeStr = item.file_size_mb ? `${item.file_size_mb} MB` : "";

      el.innerHTML = `
        <div class="history-item-left">
          <div class="history-track-icon">🎵</div>
          <div class="history-meta-wrap">
            <span class="history-title" title="${item.title}">${item.title}</span>
            <span class="history-artist" title="${item.artist}">${item.artist}</span>
            <span class="history-subinfo">${item.created_at || ""} • ${sizeStr}</span>
          </div>
        </div>

        <div class="history-item-mid">
          <span class="history-pill">${styleName}</span>
          <span class="history-pill">${mapperName}</span>
          ${bpmStr ? `<span class="history-pill">${bpmStr}</span>` : ""}
          <span class="history-stars-badge" title="Dificultad calculada oficialmente con rosu-pp">${realStarsStr}</span>
        </div>

        <div class="history-item-right">
          <a href="${item.download_url}" class="btn-history-dl" download>📥 Descargar</a>
          <button type="button" class="btn-history-del" title="Eliminar del historial">🗑️</button>
        </div>
      `;

      // Evento de eliminación
      const btnDel = el.querySelector(".btn-history-del");
      btnDel.onclick = async () => {
        if (!confirm(`¿Eliminar "${item.title}" del historial?`)) return;
        try {
          const delRes = await fetch(`/api/history/${item.job_id}`, { method: "DELETE" });
          if (delRes.ok) {
            loadHistory();
          }
        } catch (err) {
          console.error("Error al eliminar item del historial:", err);
        }
      };

      historyList.appendChild(el);
    });

  } catch (err) {
    console.error("Error cargando historial:", err);
  }
}

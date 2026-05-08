# Roadmap: Dominando la Estadística Bayesiana

Para decir que "sabes" estadística bayesiana y poder aplicarla en Machine Learning (especialmente en Probabilistic Graphical Models), debes dominar una serie de conceptos que van desde la filosofía básica hasta métodos computacionales avanzados. 

Aquí tienes la lista de verificación (checklist) ordenada por nivel de dificultad:

## 1. Fundamentos y Filosofía (El Cambio de Paradigma)
Antes de las matemáticas, debes entender cómo piensa un bayesiano:
- [ ] **Frecuentista vs. Bayesiano:** Entender que para un frecuentista, la probabilidad es la frecuencia de un evento tras infinitos intentos (los parámetros son fijos, los datos son aleatorios). Para un bayesiano, la probabilidad es el **grado de creencia** (los datos son fijos, los parámetros son variables aleatorias).
- [ ] **Regla de Bayes para eventos simples:** Entender la fórmula $P(A|B) = \frac{P(B|A)P(A)}{P(B)}$ aplicada a problemas clásicos (ej. falsos positivos en test médicos).

## 2. La Anatomía de la Inferencia Bayesiana
Debes conocer y saber calcular cada pieza del Teorema de Bayes aplicado a distribuciones continuas: $P(\theta | X) = \frac{P(X | \theta) P(\theta)}{P(X)}$
- [ ] **El Prior (A Priori) - $P(\theta)$:** Cómo codificar matemáticamente tus creencias antes de ver los datos (Priors informativos, débilmente informativos y no informativos/objetivos).
- [ ] **El Likelihood (Verosimilitud) - $P(X | \theta)$:** La función que evalúa qué tan probables son los datos observados bajo ciertos parámetros.
- [ ] **El Posterior (A Posteriori) - $P(\theta | X)$:** Tu nueva creencia actualizada. Es el gran objetivo de toda la estadística bayesiana.
- [ ] **La Evidencia (Marginal Likelihood) - $P(X)$:** El denominador. Entender por qué calcular esta integral en múltiples dimensiones es el "gran problema" que hace difícil la estadística bayesiana.

## 3. Distribuciones y Priors Conjugados (La solución analítica)
Antes de usar ordenadores potentes, los estadísticos usaban "trucos" matemáticos para evitar calcular la integral de la Evidencia.
- [ ] **Familias de Distribuciones:** Dominar la distribución Gaussiana, Binomial, Poisson. Y especialmente las distribuciones sobre distribuciones: **Beta** (para probabilidades de 0 a 1) y **Dirichlet** (para múltiples categorías, vital en NLP y PGMs).
- [ ] **Priors Conjugados:** Entender la "magia" matemática donde, si eliges el Prior correcto para un Likelihood específico, el Posterior pertenece a la misma familia que el Prior (ej. Prior Beta + Likelihood Binomial = Posterior Beta). Esto permite calcular el Posterior a mano, sin integrales complejas.

## 4. Inferencia y Toma de Decisiones
Una vez tienes el Posterior, ¿qué haces con él?
- [ ] **Estimaciones Puntuales:** Entender la diferencia entre la Media del Posterior y el **MAP** (Maximum A Posteriori - la moda de la distribución). Saber que el Machine Learning tradicional (L2 Regularization) es en realidad una estimación MAP con un prior Gaussiano.
- [ ] **Intervalos de Credibilidad (HDI):** Comprender por qué los "Intervalos de Confianza" frecuentistas no significan lo que la gente cree, y cómo los Intervalos de Credibilidad Bayesianos sí te dicen: "Hay un 95% de probabilidad de que el valor real esté aquí dentro".
- [ ] **Predicción Posterior (Posterior Predictive Distribution):** Cómo usar tu modelo actualizado para predecir futuros datos integrando sobre toda la incertidumbre de los parámetros.

## 5. Métodos Computacionales Modernos (Cuando la matemática falla)
En problemas reales (y en PGMs complejos), no hay Priors Conjugados y la integral de la Evidencia es incalculable. Aquí entra la computación:
- [ ] **MCMC (Markov Chain Monte Carlo):** El algoritmo que salvó a la estadística bayesiana. Entender cómo "muestrear" del Posterior sin calcular la Evidencia.
    - *Algoritmos a conocer:* Metropolis-Hastings y Gibbs Sampling. (Súper importantes para inferencia aproximada en PGMs).
    - *Avanzados:* Hamiltonian Monte Carlo (HMC) y NUTS (usados en librerías modernas como Stan o PyMC).
- [ ] **Inferencia Variacional (Variational Inference - VI):** La alternativa rápida a MCMC. Consiste en convertir el problema de integración en un problema de optimización. (Concepto crucial si alguna vez quieres estudiar Variational Autoencoders - VAEs en Deep Learning).

## 6. Modelado Jerárquico (Multilevel Models)
El superpoder definitivo de la estadística bayesiana.
- [ ] Entender cómo modelar datos que están agrupados en jerarquías (ej. estudiantes dentro de clases, dentro de colegios).
- [ ] Comprender el concepto de **"Partial Pooling"** (Agrupamiento parcial), donde los grupos con pocos datos "toman prestada" fuerza estadística de los grupos más grandes a través de un hiper-prior compartido.

---
### Resumen del nivel de maestría:
*   **Nivel Básico:** Entiendes la diferencia con la estadística clásica, sabes actualizar probabilidades simples con el Teorema de Bayes y conoces los Priors Conjugados simples (Beta-Binomial).
*   **Nivel Intermedio (Suficiente para el curso de PGMs):** Entiendes MAP, Likelihood, Marginalización, y comprendes la intuición detrás de Gibbs Sampling (MCMC) para hacer inferencia.
*   **Nivel Avanzado:** Sabes programar un modelo jerárquico en `PyMC` o `Stan`, y entiendes la matemática de la Inferencia Variacional.

# Upload instructions

The calculations and LaTeX source are prepared. One required setting remains: add the actual GitHub repository URL in `config.tex` before the final compile.

## 1. Create the GitHub repository

1. Sign in as `tbruffy` and open https://github.com/new.
2. Create a repository, for example `econometrics-ps3`. Choose the visibility required by the course; if private, give the grader access.
3. Unzip `PS3_GitHub.zip`. Upload the **contents** of that extracted folder using **Add file → Upload files**. Preserve the folders. Uploading the ZIP itself does not unpack it on GitHub.
4. Commit the files. Copy the actual repository URL from your browser.

The GitHub package includes the solutions, code, original input data, generated results, and compiled PDF. It excludes the local Python environment and downloaded compiler.

Official GitHub file-upload guide:
https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository

## 2. Upload the LaTeX project to Overleaf

1. Open your Overleaf project dashboard.
2. Select **New project → Existing project (.zip)** (some interfaces call this **Upload Project**).
3. Upload `PS3_Overleaf.zip` directly; do not unzip it first.
4. Select `main.tex` as the main document. Use **pdfLaTeX**.
5. Open `config.tex`. Check the author name and replace the empty repository URL with the actual URL, for example:

```tex
\newcommand{\SubmissionName}{Travis Bruffy}
\newcommand{\RepositoryURL}{https://github.com/tbruffy/econometrics-ps3}
```

Use that example URL only if you created that exact repository. Add a student number to the name line if the course requires one.

6. Recompile. The reminder on the first page will be replaced by a clickable GitHub link.
7. Download the resulting PDF and name it `PS3_Travis_Bruffy.pdf`.

Official Overleaf guides:
- https://docs.overleaf.com/managing-projects-and-files/uploading-a-project
- https://docs.overleaf.com/getting-started/recompiling-your-project/the-main-document

## 3. Final submission

1. Open the downloaded PDF. Check the author line and click the GitHub link.
2. Replace `config.tex` and `submission/PS3_Travis_Bruffy.pdf` in GitHub with the final versions.
3. Upload the final PDF to the course submission portal before 22:00.
4. If the portal asks for the repository link separately, paste the same URL.
5. Keep the submission receipt.

No code execution is required for these upload steps. The Overleaf ZIP already contains all required tables.

## If time is very short

Create the GitHub repository and upload its files, upload the Overleaf ZIP, paste the repository URL into `config.tex`, recompile, and submit that PDF. These are the essential remaining steps.

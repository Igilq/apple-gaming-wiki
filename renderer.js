document.getElementById('updateDatabase').addEventListener('click', async () => {
    console.log('Update Database button clicked.');
    try {
        const response = await window.api.fetch('http://localhost:5000/update-database', { method: 'POST' });
        console.log('Server response:', response);
        alert(response.message || response.error);
    } catch (error) {
        console.error('Error updating the database:', error);
        alert('An error occurred while updating the database.');
    }
});